from collections import deque
from itertools import permutations, product
from queue import Queue
from random import randint

import curver

from .extensions import word_accepting_FSM, action_FSM, CNF_FSM
from .extensions import FirstInClass

EMPTY_TUPLE = tuple()

class WordGenerator():
    # A generator is a string (of length one).
    # A letter is a number.
    # A word is a tuple of letters.
    def __init__(self, generators, MCG_automorphisms, MCG_must_contain, word_filter, surfaces, options, inverse_generators=None):
        self.letter_generators = generators
        self.letter_inverse_generators = inverse_generators if inverse_generators is not None else self.letter_generators.swapcase()
        
        self.generators = [i for i in range(len(self.letter_generators))]
        self.letter_lookup = {letter: index for index, letter in enumerate(self.letter_generators)}
        
        self.inverse_lookup = [self.letter_lookup[letter] for letter in self.letter_inverse_generators]
        
        self.MCG_must_contain = set(frozenset(self.repr_word(clause)) for clause in MCG_must_contain.split('^'))
        
        self.word_filter = word_filter
        self.options = options
        self.surfaces = surfaces
        
        self.valid_starting_characters = set(letter for letter in self.generators if not any(all(term < letter for term in clause) for clause in self.MCG_must_contain))
        
        # We find (some of) the major relators:
        if self.options.show_progress: print('Listing relators.')
        relators = []
        for a, b in permutations(self.generators, r=2):
            A, B = self.inverse_lookup[a], self.inverse_lookup[b]
            al, bl = self.letter_generators[a], self.letter_generators[b]
            a_lam = self.surfaces.curver.curves.get(al, self.surfaces.curver.arcs.get(al))
            b_lam = self.surfaces.curver.curves.get(bl, self.surfaces.curver.arcs.get(bl))
            if a_lam is None or b_lam is None: continue
            if not (isinstance(a_lam, curver.kernel.Arc) and isinstance(b_lam, curver.kernel.Arc)) and a_lam.intersection(b_lam) == 0:
                relators.append(((a, b), (b, a)))
            if isinstance(a_lam, curver.kernel.Curve) and isinstance(b_lam, curver.kernel.Curve) and a_lam.intersection(b_lam) == 1:
                relators.append(((a, b, a), (b, a, b)))
                relators.append(((A, b, b, a), (b, a, a, B)))
                # relators.append(((A, b, b, b, a), (b, a, a, a, B)))
            if isinstance(a_lam, curver.kernel.Arc) and isinstance(b_lam, curver.kernel.Curve) and a_lam.intersection(b_lam) == 1:
                relators.append(((a, b, a, b), (b, a, b, a)))
                for l, r in product(self.generators, repeat=2):
                    ll, rl = self.letter_generators[l], self.letter_generators[r]
                    if self.surfaces.curver(al+bl+al+bl) == self.surfaces.curver(ll+rl):
                        L, R = self.inverse_lookup[l], self.inverse_lookup[r]
                        relators.append(((a, b, a), (l, B, r)))
                        relators.append(((b, a, b), (l, A, r)))
                        # relators.append(((L, b, a), (r, A, B)))
                        # relators.append(((R, b, a), (l, A, B)))
                        # relators.append(((L, a, b), (r, B, A)))
                        # relators.append(((R, a, b), (l, B, A)))
        
        # Now get all the different 'flavours' of each relator.
        def shuffle_relators(relators):
            shuffle_relator = lambda a, b: set((a[i:]+self.inverse(b[len(b)-i:]), self.inverse(a[:i])+b[:len(b)-i]) for i in range(len(a)))
            
            R = set(relators)
            S = set((x, y) for (a, b) in R for (x, y) in shuffle_relator(a, b) if all(m not in x for (m, n) in R))
            R = R.union(set((a, b) for (a, b) in S if all(x not in a or (x, y) == (a, b) for (x, y) in S)))
            R = R.union(set((self.inverse(a), self.inverse(b)) for (a, b) in R))
            R = R.union(set((b, a) for (a, b) in R))
            
            return list(R)

        relators = shuffle_relators(relators)
        balanced_relators = dict(relator for relator in relators if len(relator[0]) == len(relator[1]))
        self.find_balanced_relators_FSM = word_accepting_FSM(self.generators, balanced_relators, transform=balanced_relators.get)
        self.longest_relator = max(len(a) for a in balanced_relators)
        
        # Let's build some FSM to help us search for these faster.
        self.curver_action = {letter: self.surfaces.curver(self.letter_generators[letter]) for letter in self.generators}
        
        def find_bad(length, comparison):
            apply_action = lambda action, element: (action(element[0]), action.homology_matrix().dot(element[1]))
            convert = lambda X: (X[0], tuple(X[1].flatten()))  # Since numpy.ndarrays are not hashable we need a converter.
            
            image = {EMPTY_TUPLE: (self.surfaces.curver.triangulation.as_lamination(), self.surfaces.curver('').homology_matrix())}  # word |--> image
            best = {convert(image[EMPTY_TUPLE]): EMPTY_TUPLE}  # mapping class |--> best word.
            bad = set()  # word such that comparison(best[word], word)
            Q = Queue()
            Q.put(EMPTY_TUPLE)
            while not Q.empty():
                g = Q.get()
                if g in bad: continue
                
                for generator in self.generators:
                    word = (generator,) + g
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
        self.simpler_FSM = word_accepting_FSM(self.generators, find_bad(length=5, comparison=lambda a, b: len(a) < len(b)))
        
        # Secondly, the bad_prefix FSM detects relations whose output is earlier than its input.
        # These cannot appear in any first_in_class word or prefix.
        if self.options.show_progress: print('Bad prefix FSM')
        self.bad_prefix_FSM = word_accepting_FSM(self.generators, find_bad(length=5, comparison=lambda a, b: (len(a), a) < (len(b), b)))
        
        # Now construct a machine for determining whether a word is first in its class.
        MCG_automorphisms = [automorphism.rpartition(':') for automorphism in MCG_automorphisms.split('|')]
        self.FIC = FirstInClass(self.generators, self.inverse_lookup, self.longest_relator, self.find_balanced_relators_FSM, self.bad_prefix_FSM, self.simpler_FSM, [(list(self.repr_word(missing)), list(self.repr_word(output))) for missing, _, output in MCG_automorphisms])
        
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
        
        nodes = [EMPTY_TUPLE]
        upwards[EMPTY_TUPLE] = EMPTY_TUPLE
        for _ in range(self.options.suffix_depth):
            # Compute all the children of the current nodes.
            children = dict((word, [word + (letter,) for letter in self.generators if not self.bad_prefix_FSM.hit(word + (letter,))]) for word in nodes)
            
            self.first_child.update((node, (children[node][0][-1],)) for node in nodes)
            
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
        
        self.first_child.update((node, next((letter,) for letter in self.generators if not self.bad_prefix_FSM.hit(node + (letter,)))) for node in nodes)
    
    def inverse(self, word):
        return tuple(self.inverse_lookup[letter] for letter in word[::-1])
    
    def str_word(self, word):
        ''' Convert tuple |--> str. '''
        return ''.join(self.letter_generators[letter] for letter in word)
    
    def repr_word(self, word):
        ''' Convert str |--> tuple. '''
        return tuple(self.letter_lookup[letter] for letter in word)
    
    def valid_prefix(self, word, depth):
        ''' Return whether the given word is a valid prefix. '''
        
        if word[0] not in self.valid_starting_characters: return False
        if self.cnf_FSM.distance(word) > depth - len(word): return False
        
        if not self.FIC.is_first(word, True, self.options.largest_class_prefix): return False
        
        return True
    
    def valid_word(self, word):
        ''' Return whether the given word is valid. '''
        
        if not self.cnf_FSM.hit(word): return False
        if self.loop_invariant_FSM.has_cycle(word, self.options.basic_search_range): return False
        
        if not self.word_filter(self, word): return False
        if not self.FIC.is_first(word, False, self.options.largest_class): return False
        
        return True
    
    def valid_suffixes(self, prefix, prefix_depth, word_depth):
        ''' Returns two lists of words all of which begin with `prefix`:
        - The first is the list of all valid words of length at most `prefix_depth`.
        - The second is the list of all words of length `prefix_depth` that are valid prefixes of words of length `word_depth`.
        
        Note we require that len(prefix) < depth <= word_depth. '''
        
        prefix = self.repr_word(prefix)
        assert len(prefix) < prefix_depth <= word_depth
        
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
            if self.options.show_progress and not randint(0, self.options.progress_rate): print('\rTraversing word tree: %s          ' % self.str_word(strn), end='')
            
            # Testing validity is the slowest bit.
            strn_valid_word = self.valid_word(strn)
            strn_valid_prefix = strn_valid_word or self.valid_prefix(strn, word_depth)
            
            if strn_valid_word: output_words.append(self.str_word(strn))
            if strn_valid_prefix and len(strn) == prefix_depth: output_prefixes.append(self.str_word(strn))
            
            if strn_valid_prefix and len(strn) < prefix_depth:  # Go deeper.
                strn += self.first_child[strn[-self.options.suffix_depth:]]
            else:
                strn = backtrack(strn)
        
        return output_words, output_prefixes

