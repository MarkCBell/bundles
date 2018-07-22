##### Required modules:
from __future__ import print_function
from random import choice, seed
from time import time
try:
	from Queue import Queue
except ImportError:
	from queue import Queue
from bundler.ordering import short_lex
from bundler.extensions import build_c_FSM

class Aut_Fn():
	''' This stores a collection of automorphisms of a free group F_n. When S is a punctured
	surface then \pi_1(S) is a free group and MCG(S) acts on \pi_1(S) by automorphisms.
	
	If S isn't punctured then \pi_1(S) isn't free and canonical may not produce a canonical
	representative, however:
		1) It 'rarely' fails to produce the canonical representative for a word.
		2) generate_FSM_info below doesn't actually require canonical representatives for every word.
			only that v & w have same canonical representative => v ~ w. Which this does.
		3) The performance gain is huge. '''
	
	def __init__(self, Pi_1_generators, Twists=None):
		self.generators = Pi_1_generators
		self.trivial_relations = [generator + self.inverse(generator) for generator in Pi_1_generators]
		self.inverse_letters = dict(zip(Pi_1_generators, map(self.inverse, Pi_1_generators)))
		self.ordering = short_lex(Pi_1_generators)
		self.actions = dict()
		
		if Twists is not None:
			for curve in Twists:
				self.add_action(curve, Twists[curve])
	
	def canonical(self, w):
		w = self.cyclic_free_reduce(w)
		return self.ordering.cyclic_first_permutation(w, self.inverse(w))
	
	def add_action(self, Action_name, Action):
		''' Adds an action on this group to the groups action database. '''
		# Create a dictionary with default values.
		d = dict(zip(self.generators, self.generators))
		
		for letter in Action:
			d[letter] = self.free_reduce(Action[letter])
			d[self.inverse(letter)] = self.free_reduce(self.inverse(Action[letter]))
		
		self.actions[Action_name] = d
	
	def cyclic_free_reduce(self, word):
		word = self.free_reduce(word)  # We assume that the word is already free reduced.
		len_word = len(word)
		for i in range(len_word):
			if word[i] != self.inverse_letters[word[len_word-i-1]]:
				return word[i:len_word-i]
		
		return ''
	
	def inverse(self, word):
		return word[::-1].swapcase()
	
	def free_reduce(self, word):
		loop = True
		while loop:
			loop = False
			for i in self.trivial_relations:
				if i in word:
					word = word.replace(i, '')
					loop = True
		
		return word
	
	def apply_to(self, action_name, w):
		''' Applies an action to the loop w. '''
		action = self.actions[action_name]
		return self.free_reduce(''.join([action[letter] for letter in w]))
	
	def word_compose(self, word):
		d = dict(zip(self.generators, self.generators))
		for w in word:
			d = self.compose(d, self.actions[w])
		
		return d
	
	def compose(self, f, g, on_left=True):
		if not on_left: f, g = g, f
		d = {}
		for generator in self.generators:
			d[generator] = self.free_reduce(''.join([f[letter] for letter in g[generator]]))
		
		return d
	
	def decompose(self, aut, look_depth=3, max_look_depth=5):
		scoring = lambda dic: sum(len(dic[x])**2 for x in dic)  # How to rank isomorphisms.
		on_left = True
		decomposed, decomposing = [], ''
		
		word_images = [dict() for i in range(look_depth+1)]
		word_images[0][''] = dict(aut)  # Work with a copy of aut.
		word_scores = {'':scoring(word_images[0][''])}
		for i in range(1, look_depth+1):
			for word in word_images[i-1]:
				d2 = word_images[i-1][word]
				for x in self.actions:
					next_word = word+x
					word_images[i][next_word] = self.compose(self.actions[x], dict(d2), on_left)
					word_scores[next_word] = scoring(word_images[i][next_word])
		
		while any(word_images[0][''][x] != x for x in word_images[0]['']):  # while word_images[0][''] is not Id.
			m = min((word_scores[word], len(word)) for word in word_scores)
			next_jump = choice([word for word in word_scores if (word_scores[word], len(word)) == m])
			
			if next_jump == '':
				if decomposing == '':
					if look_depth < max_look_depth:
						look_depth += 1
						word_images.append(dict())
					else:
						return []
				
				decomposed.append(decomposing)
				decomposing = ''
				on_left = not on_left
				
				# Reset EVERYTHING!
				for i in range(1, look_depth+1):
					for word in word_images[i-1]:
						d2 = word_images[i-1][word]
						for x in self.actions:
							next_word = word+x
							word_images[i][next_word] = self.compose(self.actions[x], dict(d2), on_left)
							word_scores[next_word] = scoring(word_images[i][next_word])
			else:
				next_letter = next_jump[0]
				decomposing = next_letter + decomposing if on_left else decomposing + next_letter
				
				# Shuffle everything down.
				for i in range(0, look_depth):
					for word in word_images[i]:
						next_word = next_letter+word
						word_images[i][word] = word_images[i+1][next_word]
						word_scores[word] = word_scores[next_word]
				
				# Calculate the new boundary values.
				for word in word_images[look_depth-1]:
					d2 = word_images[look_depth-1][word]
					for x in self.actions:
						next_word = word+x
						word_images[look_depth][next_word] = self.compose(self.actions[x], dict(d2), on_left)
						word_scores[next_word] = scoring(word_images[look_depth][next_word])
		
		decomposed.append(decomposing)
		decomposing = ''
		return self.inverse(''.join(decomposed[::2][::-1])) + self.inverse(''.join(decomposed[1::2]))

##### FSM code

def generate_FSM_info(MCG_generators, seeds, depth, Pi_1_action):
	''' Generates a FSM consisting of all loops within distance n of an element of the seed. '''
	
	Machine = []
	reduced_seeds = [Pi_1_action.canonical(w) for w in seeds]
	Loop_names = set()
	Unexplored = Queue()
	for seed in reduced_seeds:
		if seed not in Loop_names:
			Unexplored.put(seed)
			Loop_names.add(seed)
	Depth = dict((w, 0) for w in reduced_seeds)
	
	while not Unexplored.empty():
		current_loop = Unexplored.get()
		current_depth = Depth[current_loop]
		
		arrows = {'':current_loop}  # We store the current loops name in the '' field.
		
		# Determine the action of each of mcg_generators of the current_loop.
		for generator in MCG_generators:  # We explore in every direction.
			new_loop = Pi_1_action.canonical(Pi_1_action.apply_to(generator, current_loop))
			
			arrows[generator] = new_loop
			if current_depth < depth and new_loop not in Loop_names:
				Unexplored.put(new_loop)
				Loop_names.add(new_loop)
				Depth[new_loop] = current_depth + 1
		
		Machine.append(arrows)
	
	return build_c_FSM(MCG_generators, Machine)

