
''' For solving the conjugacy problem in Right Angled Artin Groups (RAAGs).
See:
	The conjugacy problem in subgroups of right-angled Artin groups
	http://perso.univ-rennes1.fr/bertold.wiest/ConjuLin.pdf

We use these as the mapping class group of a surface is an Artin group,
therefore we may ignore any relations that are not commutators and obtain
a RAAG. If two words are equivalent in the group then they are equivalent
in the MCG; this helps us to discard words. However, the converse is not 
true and so we may miss many equivalences. Thus this only helps our standard
tests and is not a substitue for them. 

TO DO:
	Replace this module with one that works on Artin Groups (possibly of 
small or finite type).
'''

##### Required modules:
from __future__ import print_function
from itertools import product, chain
from collections import deque

flip = lambda x: (x[1], x[0])
diagonalise = lambda x: (x, x)

class RAAG:
	def __init__(self, alphabet, commuters, alphabet_inverse=None):
		if alphabet_inverse is None: alphabet_inverse = alphabet.swapcase()
		
		self.alphabet = alphabet
		self.alphabet_inverse = alphabet_inverse
		self.encoded_lookup = dict()
		for i, (w, w_i) in enumerate(zip(self.alphabet, self.alphabet_inverse)):
			self.encoded_lookup[w] = (i+1, +1)
			self.encoded_lookup[w_i] = (i+1, -1)
		
		self.num_generators = len(alphabet)
		self.generators = range(1, 1+self.num_generators)
		self.num_dummy_generators = self.num_generators + 1
		self.dummy_generators = range(0, self.num_dummy_generators)
		
		translated_commuters = [(self.encoded_lookup[a][0], self.encoded_lookup[b][0]) for a, b in commuters]
		self.commuters = set(chain(translated_commuters, map(flip, translated_commuters), map(diagonalise, self.generators)))
		
		self.non_commuters = dict(zip(self.generators, [set() for i in self.generators]))
		self.non_commuters_and_i = dict(zip(self.generators, [set() for i in self.generators]))
		for i, j in product(self.generators, self.generators):
			if (i, j) not in self.commuters:
				self.non_commuters[i].add(j)
				self.non_commuters_and_i[i].add(j)
			if i == j:
				self.non_commuters_and_i[i].add(j)
		
		
		# We use deques for fast access at the front and back.
		# We'll keep one bucket empty so we can use natural indexing.
		self.piles = [deque() for i in self.dummy_generators]
		self.clear_piles()
	
	def clear_piles(self):
		self.pile_count = 0
		for i in self.generators:
			self.piles[i].clear()
	
	def piling(self, word, quick_exit=False):
		for w in word:
			i, epsilon = self.encoded_lookup[w]
			
			if self.piles[i] and self.piles[i][-1] == -epsilon:
				if quick_exit:
					self.clear_piles()
					return False
				self.pile_count -= 1
				for j in self.non_commuters_and_i[i]:
					self.piles[j].pop()
			else:
				self.pile_count += 1
				self.piles[i].append(epsilon)
				for j in self.non_commuters[i]:
					self.piles[j].append(0)
		
		return True
	
	def cyclic_reduce_piling(self):
		while True:
			i = 0
			for j in self.generators:
				if self.piles[j] and self.piles[j][0] and self.piles[j][0] == -self.piles[j][-1]:
					i = j
					break
			if i == 0: break
			
			self.pile_count -= 2
			for j in self.non_commuters_and_i[i]:
				self.piles[j].pop()
				self.piles[j].popleft()
		
		return True
	
	def depile(self):
		w = [None] * self.pile_count
		len_w = len(w)
		while True:
			i = 0
			for j in self.generators:
				if self.piles[j] and self.piles[j][0]:
					i = j
					break
			if i == 0: break
			
			w[len_w - self.pile_count] = self.alphabet[i-1] if self.piles[i][0] == 1 else self.alphabet_inverse[i-1]
			
			self.pile_count -= 1
			for j in self.non_commuters_and_i[i]:
				self.piles[j].popleft()
		
		return ''.join(w)
	
	def normalise(self, word, cyclic_reduce=True):
		self.piling(word)
		if cyclic_reduce: self.cyclic_reduce_piling()
		return self.depile()
	
	def cyclic_cancellation(self, word):
		front = [None] * self.num_dummy_generators
		back = [None] * self.num_dummy_generators
		
		for w in word:
			i, epsilon = self.encoded_lookup[w]
			
			if front[i] is None:
				front[i] = epsilon
			for j in self.non_commuters[i]:
				if front[j] is None:
					front[j] = 0
			
			back[i] = epsilon
			for j in self.non_commuters[i]:
				back[j] = 0
		
		for j in self.generators:
			if front[j] and back[j] and front[j] == -back[j]:
				return True
		
		return False

if __name__ == '__main__':
	G = RAAG('abcd', [('a','d'), ('b','c'), ('b','d')])
	print(G.normalise('BBDcbdabAbbD', cyclic_reduce=False))
	print(G.normalise('a', cyclic_reduce=False))
	print(G.normalise('BBDcbdabAbbD'))
	print(G.normalise('a'))
	
	import cProfile
	def test():
		G = RAAG('abcd', [('a','d'), ('b','c'), ('b','d')])
		for i in range(100000): 
			G.normalise('BBDcbdabAbbD') 
	cProfile.run('test()', sort='time')
