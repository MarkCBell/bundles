##### Required modules:
from __future__ import print_function
from random import randint
from collections import deque
from itertools import product
from bisect import bisect_right
try:
	from string import maketrans
except ImportError:
	maketrans = str.maketrans

from bundler.Aut_Fn import generate_FSM_info, Aut_Fn
from bundler.fat_graphs import load_fat_graph
from bundler.FSM import word_accepting_FSM
from bundler.RAAG import RAAG
from bundler.relators import shuffle_relators, find_bad_prefix_relators, find_simpler_relators
from bundler.ordering import short_lex
from bundler.extensions import convert_action_to_matrix, c_automorph

def extract_surface_information(surface_file_contents, MCG_generators):
	# Convention: A curve intersects itself -1 times.
	MCG_generators = [generator for generator in MCG_generators if generator.islower()]
	
	d = dict()
	for line in surface_file_contents.split('\n'):
		data = line.split('#')[0].split(',')
		if data[0] in ['annulus', 'rectangle']:
			d[data[1]] = {'type':data[0], 'inverse_name':data[2], 'intersections':set(set(abs(int(x)) for x in data[3:]))}
	
	curve_type = dict([(generator, d[generator]['type']) for generator in MCG_generators])
	
	intersection = dict([(generator, dict()) for generator in MCG_generators])
	
	for generator in MCG_generators:
		for other_generator in MCG_generators:
			if generator == other_generator:
				intersection[generator][other_generator] = -1
			else:
				intersection[generator][other_generator] = len(d[generator]['intersections'].intersection(d[other_generator]['intersections']))
	
	return curve_type, intersection

class word_generator():
	def __init__(self, MCG_generators, arc_neighbours, MCG_automorphisms, MCG_must_contain, word_filter, option, symmetric_generators=True):
		
		self.MCG_generators = MCG_generators
		self.arc_neighbours = arc_neighbours
		self.MCG_automorphisms = MCG_automorphisms
		self.MCG_must_contain = [contain.lower() for contain in MCG_must_contain]
		self.word_filter = word_filter
		self.option = option
		self.symmetric_generators = symmetric_generators
		
		# Set up rules for what a word must contain.
		self.MCG_must_contain_pure = ''.join(contain for contain in self.MCG_must_contain if len(contain) == 1)
		self.MCG_must_contain_impure = [contain for contain in self.MCG_must_contain if len(contain) != 1]
		self.MCG_must_contain_posibilities = [set(p) for p in product(*self.MCG_must_contain)]
		
		# Get an ordering system.
		self.stop_character = '~'
		self.MCG_generators_extended = self.MCG_generators + self.stop_character
		self.MCG_ordering = short_lex(self.MCG_generators_extended)
		self.translate_rule = self.MCG_ordering.translate_rule
		self.stop_character_translated = self.stop_character.translate(self.translate_rule)
		self.MCG_generators_last = self.MCG_generators[-1]
		self.MCG_generators_first = self.MCG_generators[0]
		first_valid = self.MCG_ordering.first(self.MCG_must_contain_pure+self.MCG_must_contain_pure.upper()) if self.MCG_must_contain_pure else self.MCG_generators_last
		self.valid_starting_characters = set(letter for letter in self.MCG_generators if not self.MCG_ordering(first_valid, letter))
		self.MCG_generators_translated = self.MCG_generators.translate(self.translate_rule)
		self.stop_character_translated = self.stop_character.translate(self.translate_rule)
		
		# Now construct a machine for performing automorphisms.
		self.MCG_automorphisms_always_translated = [output.translate(self.translate_rule) + self.stop_character_translated for missing, output in self.MCG_automorphisms if not missing]
		self.MCG_automorphisms_missing_translated = [(missing.translate(self.translate_rule), output.translate(self.translate_rule) + self.stop_character_translated) for missing, output in self.MCG_automorphisms if missing]
		self.c_auto = c_automorph(self.symmetric_generators, self.MCG_generators_extended.translate(self.translate_rule), self.MCG_generators_extended.swapcase().translate(self.translate_rule), self.MCG_automorphisms_always_translated, self.MCG_automorphisms_missing_translated)
		
		# We now extract the curve types and the intersections of the MCG_generators from the surface file.
		self.curve_type, self.intersection = extract_surface_information(self.option.SURFACE_FILE_CONTENTS, self.MCG_generators)
		
		# And get information about the induced action on pi_1 using a fat graph.
		if self.option.SHOW_PROGRESS: print('Generating fat graphs.')
		G = load_fat_graph(self.option.SURFACE_FILE_CONTENTS)
		self.Pi_1_generators = G.Pi_1_generators()
		self.Twist_actions_on_pi_1 = G.actions(self.MCG_generators)
		self.Twist_actions_on_H_1 = dict((g, convert_action_to_matrix(self.Pi_1_generators, self.Twist_actions_on_pi_1[g])) for g in self.MCG_generators)
		self.Homology_Cache = dict()
		for g in self.MCG_generators:
			self.Homology_Cache[g] = self.Twist_actions_on_H_1[g]
		
		self.loop_invariant_FSM_seed = G.possible_seeds()
		
		# We use this information to automatically generate some databases:
		# These are (some of) the major relators:
		if self.option.SHOW_PROGRESS: print('Listing relators.')
		self.relators = []
		self.commutors = set()
		for a in self.MCG_generators:
			if a.isupper(): continue
			for b in self.MCG_generators:
				if b.isupper(): continue
				A, B = a.upper(), b.upper()
				if self.intersection[a][b] == -1:
					self.commutors.add((a, b))
					self.commutors.add((b, a))
				if self.intersection[a][b] == 0:
					if not (self.curve_type[a] == 'rectangle' and self.curve_type[b] == 'rectangle'):
						self.relators.append((a + b, b + a))
						self.commutors.add((a, b))
						self.commutors.add((b, a))
				if self.intersection[a][b] == 1:
					if self.curve_type[a] == 'annulus' and self.curve_type[b] == 'annulus':
						self.relators.append((a + b + a, b + a + b))
						self.relators.append((A + b + b + a, b + a + a + B))
						# self.relators.append((A + b + b + b + a, b + a + a + a + B))
						# self.relators.append((A + b + b + b + b + a, b + a + a + a + a + B))
					elif self.curve_type[a] == 'rectangle' and self.curve_type[b] == 'annulus':
						if a in self.arc_neighbours and b in self.arc_neighbours[a]:
							l, r = arc_neighbours[a][b]
							L, R = l.upper(), r.upper()
							self.relators.append((a + b + a, l + B + r))
							self.relators.append((b + a + b, l + A + r))
							self.relators.append((a + b + a + b, b + a + b + a))
							self.relators.append((L + b + a, r + A + B))
							self.relators.append((R + b + a, l + A + B))
							self.relators.append((L + a + b, r + B + A))
							self.relators.append((R + a + b, l + B + A))
		
		# Now get all the different 'flavors' of each relator.
		self.relators = shuffle_relators(self.relators)
		self.relators.sort(key=lambda w: (len(w[0]), w[0].translate(self.translate_rule)))
		self.relators_translated = [(a.translate(self.translate_rule), b.translate(self.translate_rule)) for (a, b) in self.relators]
		self.relator_lookup = dict(self.relators)
		self.max_relator_len_plus_1 = max(len(r[0]) for r in self.relators) + 1
		self.find_relators = word_accepting_FSM(self.MCG_generators, [r[0] for r in self.relators])
		
		# Let's build some FSM to help us search for these faster.
		# Firstly, the simpler FSM detects relations whose output is shorter than its input.
		# Any word which contains one such input cannot be first_in_class.
		# Secondly, the bad_prefix FSM detects relations whose output is earlier than its input.
		# These cannot appear in any first_in_class word or prefix.
		if self.option.SHOW_PROGRESS: print('Finding new relators.')
		bad_prefix = find_bad_prefix_relators(self.relators, self.MCG_generators, 100, 6, self.MCG_ordering)
		simpler = find_simpler_relators(self.relators, self.MCG_generators, 100, 6, self.MCG_ordering)
		self.simpler_FSM = word_accepting_FSM(self.MCG_generators, simpler)
		self.bad_prefix_FSM = word_accepting_FSM(self.MCG_generators, bad_prefix)
		
		if self.option.SHOW_PROGRESS: print('Building FSM.')
		self.fundamental_group_action = Aut_Fn(self.Pi_1_generators, self.Twist_actions_on_pi_1)
		self.loop_invariant_FSM = generate_FSM_info(self.MCG_generators, self.loop_invariant_FSM_seed, self.option.LOOP_INVARIANT_FSM_DEPTH, self.fundamental_group_action)
		
		# Now build some dictionaries for looking up the next characters in MCG_generators.
		if option.SHOW_PROGRESS: print('Constructing suffix tree.')
		self.good_words_collated = [[''.join(p) for p in product(self.MCG_generators, repeat=i) if self.bad_prefix_FSM.evaluate(''.join(p)) >= 0] for i in range(self.option.SUFFIX_DEPTH+1)]
		self.good_words_collated_translated = [[w.translate(self.translate_rule) for w in L] for L in self.good_words_collated]
		all_good_words = [w for L in self.good_words_collated for w in L]
		
		self.next_suffix = dict()
		self.next_addable_character = dict(zip(all_good_words, map(lambda word: [letter for letter in self.MCG_generators if letter == self.MCG_generators_last or not self.bad_prefix_FSM.evaluate(word + letter) < 0][0], all_good_words)))
		# self.next_character = dict()
		
		# Set up a right-angled Artin group to quickly test for commutativity.
		MCG_generators_lower = ''.join(letter for letter in self.MCG_generators if letter.islower()) + self.stop_character
		self.RAAG_translated = RAAG(MCG_generators_lower.translate(self.translate_rule), [(a.translate(self.translate_rule), b.translate(self.translate_rule)) for a, b in self.commutors], MCG_generators_lower.upper().translate(self.translate_rule))
		
	
	# def next_addable_character(self, suffix):
		# if suffix not in self.next_character:
			# for letter in self.MCG_generators:
				# if letter == self.MCG_generators_last or not self.bad_prefix_FSM.evaluate(suffix + letter) < 0:
					# self.next_character[suffix] = letter
					# break
		
		# return self.next_character[suffix]
	
	def next_good_suffix(self, suffix):
		''' Find the next possible suffix after this one.'''
		translated_suffix = suffix.translate(self.translate_rule)
		best, best_translated = '', None
		for i in range(1, len(suffix)+1):
			j = bisect_right(self.good_words_collated_translated[i], translated_suffix)
			if j != len(self.good_words_collated_translated[i]):
				k, k_translated = self.good_words_collated[i][j], self.good_words_collated_translated[i][j]
				if best_translated is None or k_translated < best_translated:
					best, best_translated = k, k_translated
		
		return best
	
	def backtrack(self, word):
		''' Gets the next feasable vertex in the tree of words based on suffix (DFT). '''
		while True:
			suffix = word[-self.option.SUFFIX_DEPTH:]
			if suffix not in self.next_suffix: self.next_suffix[suffix] = self.next_good_suffix(suffix)
			n = self.next_suffix[suffix]
			word = word[:-self.option.SUFFIX_DEPTH] + n
			if n != '' or word == '': return word
	
	def greedy_shuffle(self, word):
		word_lower = word.lower()
		for i in range(1,len(word)-1):
			start_lower = word_lower[:i]
			d = self.MCG_ordering.lookup[word[i]]
			for j in range(i+1,len(word)-1):
				if any((a, word_lower[j-1]) not in self.commutors for a in start_lower): break
				if self.MCG_ordering.lookup[word[j]] < d:
					return word[:i] + word[j:] + word[i:j]
		
		return word
	
	def H_1_action(self, w, len_w):
		''' Uses divide and conquer to compute the product of the matrices
		specified by w. Stores the product of words smaller than the
		Homology_Cache_Threshold in the Homology_Cache to speed up later
		computations. '''
		
		threshold = self.option.H_1_CACHE_THRESHOLD
		
		if len_w <= threshold:
			if w in self.Homology_Cache:
				return self.Homology_Cache[w].copy()
			
			len_w2 = len_w // 2
			A = self.H_1_action(w[:len_w2], len_w2) * self.H_1_action(w[len_w2:], len_w - len_w2)
			self.Homology_Cache[w] = A.copy()  # If the word was small enough then save the result in the cache.
		else:
			A = self.H_1_action(w[:threshold], threshold) * self.H_1_action(w[threshold:], len_w - threshold)
		
		return A
	
	def homology_order(self, word):
		A = self.H_1_action(word[::-1], len(word))
		A.add_diagonal(-1)
		return abs(A.determinant())
	
	def first_in_class(self, word, max_tree_size=0, prefix=False):
		''' Determines if a word is lex first in its class.
		
		Uses relators and automorphs to find alternative representatives. Gives up after finding
		max_tree_size alternatives, if max_tree_size <= 0 this will run until it has found all
		equivalent words of the same length in which case the result returned is absolutly correct.
		
		If prefix == True, only prefix stable stable moves are performed, i.e. if it is discovered
		that u ~ v then uw ~ vw for all words w.
		
		This function is the heart of the grow phase, speed is critical here.'''
		
		len_word = len(word)  # Let's save some highly used data.
		
		# If it contains any bad prefix or simplification then it can be (trivially) made better.
		if self.bad_prefix_FSM.evaluate(word) < 0:
			return False
		
		if self.simpler_FSM.evaluate(word) < 0:
			return False
		
		# Modify the word if it is a prefix.
		if prefix:
			word += self.stop_character
			len_word += 1
		
		# We're going to need a translated version of the word a lot.
		translated_word = word.translate(self.translate_rule)
		
		# Check to see if our origional word beats itself.
		if not self.c_auto.before_automorphs(translated_word, translated_word, len_word, prefix):
			return False
		
		# We'll use our RAAG to quickly check for commutativity over the end.
		if not prefix and self.RAAG_translated.cyclic_cancellation(translated_word):
			return False
		
		Total = set([word])  # This records all words that we have seen.
		Unchecked = deque([word])  # This is a deque of all words that have yet to be processed.
		
		while Unchecked:  # Keep going while there are still unprocessed words in the queue.
			reached = Unchecked.popleft()  # Get the next equivalent word to check.
			
			for b, match in self.find_relators.evaluate(reached[:-1] if prefix else reached + reached, False):
				a = b - len(match)
				# There is a replacement to be made between a & b.
				if a > len_word: continue
				
				replace = self.relator_lookup[match]
				next_word = reached[:a] + replace + reached[b:] if prefix or b <= len_word else replace[len_word-a:] + reached[b-len_word:a] + replace[:len_word-a]
				
				if next_word not in Total:  # Only consider new words.
					# Test for trivial simplifications.
					if self.simpler_FSM.evaluate(next_word[:-1] if prefix else next_word + next_word[0]) < 0:
						return False
					
					if not self.c_auto.before_automorphs(translated_word, next_word.translate(self.translate_rule), len_word, prefix):
						return False
					
					# If we've hit the max_tree_size then give up.
					if len(Total) == max_tree_size: return True
					
					# Add it to the reachable word list.
					Total.add(next_word)
					Unchecked.append(next_word)
		
		return True
	
	def valid_prefix(self, word, depth, max_tree_size=None):
		''' Test to see if given word is a valid prefix. '''
		if word[0] not in self.valid_starting_characters: return False
		word_lower = word.lower()
		word_lower_set = set(word_lower)
		if min(len(p.difference(word_lower_set)) for p in self.MCG_must_contain_posibilities) > depth - len(word): return False
		
		# Now check if we can remove a really bad letter at the back.
		word_lower_without_last_set = set(word_lower[:-1])
		d = self.MCG_ordering.lookup[word_lower[-1]]
		if any(self.MCG_ordering.lookup[letter] < d and letter not in word_lower_without_last_set for letter in self.MCG_must_contain_pure):
			if all(y.isupper() or (p, y) in self.commutors for y in self.MCG_generators[d:] for p in word_lower_without_last_set):
				return False
		
		# Divide up word into: start|middle|end.
		# If end[0] < middle[0] and start and middle commute then this is not a valid prefix.
		# By earlier instances of this test it is sufficient to check when len(end) == 1.
		d = self.MCG_ordering.lookup[word[-1]]
		for i in range(1, len(word)-1):
			if d < self.MCG_ordering.lookup[word[i]]:
				word_prime = word[:i]
				word_double_prime = word[i:-1]
				if all((a, b) in self.commutors for a in word_prime.lower() for b in word_double_prime.lower()):
					return False
		
		if not self.first_in_class(word, max_tree_size if max_tree_size is not None else self.option.LARGEST_CLASS_PREFIX, True):
			return False
		
		return True
	
	def valid_word(self, word, max_tree_size=None):
		''' Test to see if given word is a valid word. '''
		word_lower_set = set(word.lower())
		
		if any(letter not in word_lower_set for letter in self.MCG_must_contain_pure): return False
		if any(all(letter not in word_lower_set for letter in contain) for contain in self.MCG_must_contain_impure): return False
		if self.loop_invariant_FSM.has_cycle(word, self.option.BASIC_SEARCH_RANGE): return False  # Note: word forms a cycle iff word[::-1] does.
		
		if self.option.ACCEPTABLE_HOMOLOGY_ORDERS and self.homology_order(word) not in self.option.ACCEPTABLE_HOMOLOGY_ORDERS: return False
		if not self.word_filter(self, word): return False
		if not self.first_in_class(word, max_tree_size if max_tree_size is not None else self.option.LARGEST_CLASS, False): return False
		
		return True
	
	def valid_suffixes(self, prefix, depth, word_depth=None):
		''' Returns 2 lists. The first is a list of all valid words which are an extension of 'prefix'
		 with length at most 'depth' while the second is the sublist consisting of those which have length
		'depth' and are also valid prefixes. Note we require that len(prefix) < depth <= word_depth. '''
		
		if word_depth is None: word_depth = depth
		assert len(prefix) < depth <= word_depth
		
		output_words = []
		output_prefixes = []
		
		prefix_len = len(prefix)
		strn = prefix + self.next_addable_character[prefix[-self.option.SUFFIX_DEPTH:]]
		while strn and strn[:prefix_len] == prefix:
			if self.option.SHOW_PROGRESS and not randint(0,self.option.PROGRESS_RATE_GROW): print('\rTraversing word tree: %s          ' % strn, end='')
			
			# Testing validity is the slowest bit.
			strn_valid_word = self.valid_word(strn)
			
			if strn_valid_word: output_words.append(strn)
			
			if len(strn) == word_depth:
				strn = self.backtrack(strn)
			elif strn_valid_word or self.valid_prefix(strn, word_depth):  # valid_word ==> valid_prefix.
				if len(strn) == depth:
					output_prefixes.append(strn)
					strn = self.backtrack(strn)
				else:
					strn += self.next_addable_character[strn[-self.option.SUFFIX_DEPTH:]]
			else:
				strn = self.backtrack(strn)
		
		return output_words, output_prefixes

