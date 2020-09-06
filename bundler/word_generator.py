
from collections import deque
from itertools import permutations, product
from queue import Queue
from random import randint

from sympy import eye
import curver

from .decorators import memoize
from .extensions import word_accepting_FSM, action_FSM, CNF_FSM, Automorph, ShortLex

STOP = '~'

def shuffle_relators(relators):
    inverse = lambda word: word[::-1].swapcase()
    shuffle_relator = lambda a, b: set((a[i:]+inverse(b[len(b)-i:]), inverse(a[:i])+b[:len(b)-i]) for i in range(len(a)))
    
    R = set(relators)
    S = set((x, y) for (a, b) in R for (x, y) in shuffle_relator(a, b) if all(m not in x for (m, n) in R))
    R = R.union(set((a, b) for (a, b) in S if all(x not in a or (x, y) == (a, b) for (x, y) in S)))
    R = R.union(set((inverse(a), inverse(b)) for (a, b) in R))
    R = R.union(set((b, a) for (a, b) in R))
    
    return list(R)

class WordGenerator():
    def __init__(self, generators, MCG_automorphisms, MCG_must_contain, word_filter, surfaces, options, symmetric_generators=True):
        self.generators = generators
        self.MCG_automorphisms = MCG_automorphisms
        self.MCG_must_contain = set(frozenset(clause) for clause in MCG_must_contain.split('^'))
        self.word_filter = word_filter
        self.options = options
        self.surfaces = surfaces
        self.symmetric_generators = symmetric_generators  # Whether word and word.swapcase() are equivalent same mapping classes.
        
        # Get an ordering system.
        assert all(generator < STOP for generator in self.generators)
        generators_extended = self.generators + STOP
        self.ordering = ShortLex(generators_extended)
        self.valid_starting_characters = set()
        for letter in self.generators:
            self.valid_starting_characters.add(letter)
            if frozenset([letter, letter.swapcase()] if self.symmetric_generators else [letter]) in self.MCG_must_contain:  # Recheck this.
                break
        
        # Now construct a machine for performing automorphisms.
        automorphisms = [automorphism.rpartition(':') for automorphism in self.MCG_automorphisms]
        self.c_auto = Automorph(
            self.ordering.translate(generators_extended),
            self.ordering.translate(generators_extended.swapcase()),
            [(self.ordering.translate(missing), self.ordering.translate(output + STOP)) for missing, _, output in automorphisms]
            )
        
        # We find (some of) the major relators:
        if self.options.show_progress: print('Listing relators.')
        relators = []
        lower_generators = [generator for generator in self.generators if generator.islower()]
        for a, b in permutations(lower_generators, r=2):
            A, B = a.upper(), b.upper()
            a_lam = self.surfaces.curver.curves.get(a, self.surfaces.curver.arcs.get(a))
            b_lam = self.surfaces.curver.curves.get(b, self.surfaces.curver.arcs.get(b))
            if not (isinstance(a_lam, curver.kernel.Arc) and isinstance(b_lam, curver.kernel.Arc)) and a_lam.intersection(b_lam) == 0:
                relators.append((a+b, b+a))
            if isinstance(a_lam, curver.kernel.Curve) and isinstance(b_lam, curver.kernel.Curve) and a_lam.intersection(b_lam) == 1:
                relators.append((a+b+a, b+a+b))
                relators.append((A+b+b+a, b+a+a+B))
                # relators.append((A+b+b+b+a, b+a+a+a+B))
            if isinstance(a_lam, curver.kernel.Arc) and isinstance(b_lam, curver.kernel.Curve) and a_lam.intersection(b_lam) == 1:
                relators.append((a+b+a+b, b+a+b+a))
                for l, r in product(lower_generators, repeat=2):
                    if self.surfaces.flipper(a+b+a+b) == self.surfaces.flipper(l+r):
                        L, R = l.upper(), r.upper()
                        relators.append((a + b + a, l + B + r))
                        relators.append((b + a + b, l + A + r))
                        relators.append((L + b + a, r + A + B))
                        relators.append((R + b + a, l + A + B))
                        relators.append((L + a + b, r + B + A))
                        relators.append((R + a + b, l + B + A))
        # Now get all the different 'flavors' of each relator.
        relators = shuffle_relators(relators)
        balanced_relators = [relator for relator in relators if len(relator[0]) == len(relator[1])]
        
        self.balanced_relator_lookup = dict(balanced_relators)
        self.find_balanced_relators_FSM = word_accepting_FSM(self.generators, [a for a, _ in balanced_relators])
        
        # Let's build some FSM to help us search for these faster.
        self.curver_action = {letter: self.surfaces.curver(letter) for letter in self.generators}
        
        def find_bad(length, comparison):
            apply_action = lambda action, element: (action(element[0]), action.homology_matrix().dot(element[1]))
            convert = lambda X: (X[0], tuple(X[1].flatten()))  # Since numpy.ndarrays are not hashable we need a converter.
            
            image = {'': (self.surfaces.curver.triangulation.as_lamination(), self.surfaces.curver('').homology_matrix())}  # word |--> image
            best = {convert(image['']): ''}  # mapping class |--> best word.
            bad = set()  # word such that comparison(best[word], word)
            Q = Queue()
            Q.put('')
            while not Q.empty():
                g = Q.get()
                if g in bad: continue
                
                for generator in self.generators:
                    word = generator + g
                    if any(word[:i] in bad for i in range(1, len(word))): continue
                    
                    neighbour = apply_action(self.curver_action[generator], image[g])
                    key = convert(neighbour)
                    if key in best:
                        # Can be neither, but can't be both.
                        if comparison(best[key], word):
                            bad.add(word)
                            # best[key] = best[key]
                        elif comparison(word, best[key]):
                            bad.add(best[key])
                            best[key] = word
                            if len(word) < length:  # Seach deeper.
                                image[word] = neighbour
                                Q.put(word)
                    else:  # element not seen yet.
                        best[key] = word
                        if len(word) < length:  # Seach deeper.
                            image[word] = neighbour
                            Q.put(word)
            
            return bad
        
        # Firstly, the simpler FSM detects relations whose output is shorter than its input.
        # Any word which contains one such input cannot be first_in_class.
        if self.options.show_progress: print('Building FSMs')
        if self.options.show_progress: print('Simpler FSM')
        self.simpler_FSM = word_accepting_FSM(self.generators, find_bad(length=4, comparison=lambda b, w: len(b) < len(w)))
        
        # Secondly, the bad_prefix FSM detects relations whose output is earlier than its input.
        # These cannot appear in any first_in_class word or prefix.
        if self.options.show_progress: print('Bad prefix FSM')
        self.bad_prefix_FSM = word_accepting_FSM(self.generators, find_bad(length=4, comparison=self.ordering.cmp))
        
        if self.options.show_progress: print('Loop invariant FSM')
        seeds = self.surfaces.curver.triangulation.edge_curves()
        self.loop_invariant_FSM = action_FSM(self.curver_action, seeds, self.options.loop_invariant_fsm_depth)
        
        # Set up rules for what a word must contain.
        if self.options.show_progress: print('CNF FSM')
        self.cnf_FSM = CNF_FSM(self.generators, self.MCG_must_contain)
        
        # Now build some dictionaries for looking up the next characters in generators.
        if self.options.show_progress: print('Constructing suffix tree.')
        self.first_child = dict()
        self.sibling = dict()
        upwards = dict()
        self.last_children = set()
        
        nodes = ['']
        upwards[''] = ''
        for _ in range(self.options.suffix_depth):
            # Compute all the children of the current nodes.
            children = dict((word, [word + letter for letter in self.generators if not self.bad_prefix_FSM.hit(word + letter)]) for word in nodes)
            
            for node in nodes:
                self.first_child[node] = children[node][0][-1:]
            
            for node in nodes:
                for child_1, child_2 in zip(children[node], children[node][1:]):
                    self.sibling[child_1] = child_2
                    upwards[child_1] = child_1
                
                # The sibling of a last child is the parent, grandparent, ... that is not a last child.
                last_child = children[node][-1]
                self.sibling[last_child] = upwards[last_child] = upwards[node]
                self.last_children.add(last_child)
            
            # The new nodes are the current children.
            nodes = [child for node in nodes for child in children[node]]
        
        for node in nodes:
            self.first_child[node] = next(letter for letter in self.generators if not self.bad_prefix_FSM.hit(node + letter))
    
    @memoize(lambda word: len(word) <= 5)
    def H_1_action(self, word):
        ''' Uses divide and conquer to compute the product of the matrices specified by word.
        
        Cache small words to speed up later computations. '''
        
        if len(word) == 1:
            return self.curver_action[word].homology_matrix()
        
        # Break in half and recurse.
        midpoint = len(word) // 2
        return self.H_1_action(word[:midpoint]).dot(self.H_1_action(word[midpoint:]))
    
    def homology_order(self, word):
        A = self.H_1_action(word[::-1])
        A = A - eye(A.shape[0])
        return int(abs(A.det()))
    
    def first_in_class(self, word, max_tree_size=None, prefix=False):
        ''' Determines if a word is lex first in its class.
        
        Uses relators and automorphs to find alternative representatives. Gives up after finding
        max_tree_size alternatives, if max_tree_size <= 0 this will run until it has found all
        equivalent words of the same length in which case the result returned is absolutely correct.
        
        If prefix == True, only prefix stable stable moves are performed, i.e. if it is discovered
        that u ~ v then uw ~ vw for all words w.
        
        This function is the heart of the grow phase, speed is critical here.'''
        
        if max_tree_size is None: max_tree_size = self.options.largest_class
        len_word = len(word)  # Let's save some highly used data.
        
        # If it contains any bad prefix or simplification then it can be (trivially) made better.
        if self.bad_prefix_FSM.hit(word):
            return False
        
        # There is no point in testing whether simpler_FSM hits word already since word ended in next_good_suffix.
        
        # Modify the word if it is a prefix.
        if prefix:
            word += STOP
            len_word += 1
        
        # We're going to need a translated version of the word a lot.
        translated_word = self.ordering.translate(word)
        
        # Check to see if our original word beats itself.
        if not self.c_auto.before_automorphs(translated_word, translated_word, prefix):
            return False
        
        seen = set([word])  # This records all words that we have seen.
        to_do = deque([word])  # This is a deque of all words that have yet to be processed.
        
        while to_do:  # Keep going while there are still unprocessed words in the queue.
            reached = to_do.popleft()  # Get the next equivalent word to check.
            
            for b, match in self.find_balanced_relators_FSM.hits(reached[:-1] if prefix else reached + reached):
                a = b - len(match)
                # There is a replacement to be made between a & b.
                if a > len_word: continue
                
                replace = self.balanced_relator_lookup[match]
                next_word = reached[:a] + replace + reached[b:] if prefix or b <= len_word else replace[len_word-a:] + reached[b-len_word:a] + replace[:len_word-a]
                
                if next_word not in seen:  # Only consider new words.
                    # Test for trivial simplifications.
                    if self.simpler_FSM.hit(next_word[:-1] if prefix else next_word + next_word[0]):
                        return False
                    
                    if not self.c_auto.before_automorphs(translated_word, self.ordering.translate(next_word), prefix):
                        return False
                    
                    # If we've hit the max_tree_size then give up.
                    if len(seen) == max_tree_size: return True
                    
                    # Add it to the reachable word list.
                    seen.add(next_word)
                    to_do.append(next_word)
        
        return True
    
    def valid_prefix(self, word, depth):
        ''' Return whether the given word is a valid prefix. '''
        
        if word[0] not in self.valid_starting_characters: return False
        if self.cnf_FSM.distance(word) > depth - len(word): return False
        
        if not self.first_in_class(word, prefix=True): return False
        
        return True
    
    def valid_word(self, word):
        ''' Return whether the given word is valid. '''
        
        if not self.cnf_FSM.hit(word): return False
        if self.loop_invariant_FSM.has_cycle(word, self.options.basic_search_range): return False  # Note: word forms a cycle iff word[::-1] does.
        
        if not self.word_filter(self, word): return False
        if not self.first_in_class(word, prefix=False): return False
        
        return True
    
    def valid_suffixes(self, prefix, depth, word_depth=None):
        ''' Returns two lists. The first is a list of all valid words which are an extension of 'prefix'
         with length at most 'depth' while the second is the sublist consisting of those which have length
        'depth' and are also valid prefixes. Note we require that len(prefix) < depth <= word_depth. '''
        
        if word_depth is None: word_depth = depth
        assert len(prefix) < depth <= word_depth
        
        def backtrack(word):
            ''' Gets the next feasible vertex in the tree of words based on suffix (DFT). '''
            
            while word:
                suffix = word[-self.options.suffix_depth:]
                word = word[:-self.options.suffix_depth] + self.sibling[suffix]
                if suffix not in self.last_children: break
            
            return word
        
        output_words = []
        output_prefixes = []
        
        prefix_len = len(prefix)
        strn = prefix + self.first_child[prefix[-self.options.suffix_depth:]]
        while strn and strn[:prefix_len] == prefix:
            if self.options.show_progress and not randint(0, self.options.progress_rate): print('\rTraversing word tree: %s          ' % strn, end='')
            
            # Testing validity is the slowest bit.
            strn_valid_word = self.valid_word(strn)
            
            if strn_valid_word: output_words.append(strn)
            
            if len(strn) == word_depth:
                strn = backtrack(strn)
            elif strn_valid_word or self.valid_prefix(strn, word_depth):  # valid_word ==> valid_prefix.
                if len(strn) == depth:
                    output_prefixes.append(strn)
                    strn = backtrack(strn)
                else:
                    strn += self.first_child[strn[-self.options.suffix_depth:]]
            else:
                strn = backtrack(strn)
        
        return output_words, output_prefixes

