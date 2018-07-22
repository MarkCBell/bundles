''' This module is for manipulating and finding relators of a group. '''

##### Required modules:
from __future__ import print_function
try:
	from Queue import Queue
except ImportError:
	from queue import Queue

from itertools import product, combinations

class rewriting_system:
	def __init__(self, order, relations):
		self.relations = relations
		self.order = order
		
		self.equations = set()
		self.reductions = set()
	
	def _normalise(self, w, extra_reductions=None):
		if extra_reductions is None: extra_reductions = set()
		
		repeat = True
		while repeat:
			repeat = False
			for r1, r2 in self.reductions.union(extra_reductions):
				i = w.find(r1)
				if i > -1:
					w = w[:i] + r2 + w[i+len(r1):]
					repeat = True
					break
		
		return w
	
	# This needs a LOT of work!
	def find_new_relators(self, n, max_len=None):
		self.equations = set((e1, e2) if self.order.ordered(e2, e1) else (e2, e1) for e1, e2 in self.relations)
		self.reductions = set()
		
		while self.equations and len(self.reductions) < n:
			# print(self.equations)
			# print(self.reductions)
			# print(len(self.reductions), len(self.equations))
			e = min(self.equations, key=lambda e: len(e[0]))
			
			e1, e2 = self._normalise(e[0]), self._normalise(e[1])
			if e1 != e2:
				# Order equation.
				r = (e1, e2) if self.order.ordered(e2, e1) else (e2, e1)
				# ===============
				
				# Normalise reductions.
				set_r = set([r])
				R_remove = set(R for R in self.reductions if r[0] in R[1])
				
				self.reductions.difference_update(R_remove)
				self.reductions.update(set((R[0], self._normalise(R[1], set_r)) for R in R_remove))
				# =====================
				
				# Critical pairs.
				for r2 in self.reductions:
					for k in range(1, min(len(r[0]), len(r2[0])) + 1):
						if r[0][-k:] == r2[0][:k]:
							o1 = self._normalise(r[1] + r2[0][k:])
							o2 = self._normalise(r[0][:-k] + r2[1])
							if o1 != o2:
								if max_len is None or (len(o1) < max_len and len(o2) < max_len):
									self.equations.add((o1, o2) if self.order.ordered(o2, o1) else (o2, o1))
							break
					for k in range(1, min(len(r[0]), len(r2[0])) + 1):
						if r2[0][-k:] == r[0][:k]:
							o1 = self._normalise(r2[1] + r[0][k:])
							o2 = self._normalise(r2[0][:-k] + r[1])
							if o1 != o2:
								if max_len is None or (len(o1) < max_len and len(o2) < max_len):
									self.equations.add((o1, o2) if self.order.ordered(o2, o1) else (o2, o1))
							break
				# ===============
				
				# Collapse reductions.
				self.equations.update(set(R for R in self.reductions if r[0] in R[0]))
				self.reductions.difference_update(self.equations)
				# ====================
				
				# Add reduction.
				self.reductions.add(r)
			
			# Remove equation.
			self.equations.remove(e)
		
		return list(self.reductions) + list(self.equations)  # Dump out any outstanding equations.

def inverse(w):
	return w[::-1].swapcase()

def shuffle_relators(relators):
	shuffle_relator = lambda a,b: set((a[i:]+inverse(b[len(b)-i:]),inverse(a[:i])+b[:len(b)-i]) for i in range(len(a)))
	
	R = set(relators)
	S = set((x,y) for (a,b) in R for (x,y) in shuffle_relator(a,b) if all(m not in x for (m,n) in R))
	R = R.union(set((a,b) for (a,b) in S if all(x not in a or (x,y) == (a,b) for (x,y) in S)))
	R = R.union(set((inverse(a),inverse(b)) for (a,b) in R))
	R = R.union(set((b,a) for (a,b) in R))
	
	return list(R)

def find_bad_prefix_relators(old_relators, alphabet, n, max_len, order):
	extended_relators = old_relators + [(letter+letter.swapcase(), '') for letter in alphabet]
	RW = rewriting_system(order, extended_relators)
	
	return [x for (x,y) in RW.find_new_relators(n, max_len)]

def find_simpler_relators(old_relators, alphabet, n, max_len, order):
	# all_relators = set(old_relators + [r[::-1] for r in old_relators])
	# shorter_relators = set()
	
	# Q = Queue()
	# for r1, r2 in all_relators:
		# if len(r1) > len(r2): Q.put((r1, r2))
		# if len(r1) < len(r2): Q.put((r2, r1))
	
	# for letter in alphabet:
		# Q.put((letter+letter.swapcase(), ''))
	
	# while not Q.empty():
		# r = Q.get()
		# for r2 in all_relators:
			# for k in range(1, min(len(r[0]), len(r2[0])) + 1):
				# if r[0][-k:] == r2[0][:k]:
					# o1 = r[1] + r2[0][k:]  # Shorter.
					# o2 = r[0][:-k] + r2[1]  # Longer.
					# if o1 != o2:
						# new_r = (o2, o1)
						# if new_r not in shorter_relators:
							# if len(shorter_relators) == n: return [x for (x, y) in shorter_relators]
							# shorter_relators.add(new_r)
							# Q.put(new_r)
			
			# for k in range(1, min(len(r[0]), len(r2[0])) + 1):
				# if r2[0][-k:] == r[0][:k]:
					# o1 = r2[1] + r[0][k:]  # Longer.
					# o2 = r2[0][:-k] + r[1]  # Shorter.
					# if o1 != o2:
						# new_r = (o1, o2)
						# if new_r not in shorter_relators:
							# if len(shorter_relators) == n: return [x for (x, y) in shorter_relators]
							# shorter_relators.add(new_r)
							# Q.put(new_r)
	
	# return [x for (x, y) in shorter_relators]
	######################
	
	all_relators = set(old_relators + [r[::-1] for r in old_relators])
	shorter_relators = set()
	new_shorter_relators = set([(r1, r2) if len(r1) > len(r2) else (r2, r1) for r in all_relators if len(r[0]) != len(r[1])] + [(letter+letter.swapcase(), '') for letter in alphabet])
	# print(all_relators)
	# print(new_shorter_relators)
	
	while len(shorter_relators) + len(new_shorter_relators) < n:
		next_shorter_relators = set()
		
		for r in new_shorter_relators:
			for r2 in all_relators:
				for k in range(1, min(len(r[0]), len(r2[0])) + 1):
					if r[0][-k:] == r2[0][:k]:
						o1 = r[1] + r2[0][k:]  # Shorter.
						o2 = r[0][:-k] + r2[1]  # Longer.
						if o1 != o2: next_shorter_relators.add((o2, o1))
				
				for k in range(1, min(len(r[0]), len(r2[0])) + 1):
					if r2[0][-k:] == r[0][:k]:
						o1 = r2[1] + r[0][k:]  # Longer.
						o2 = r2[0][:-k] + r[1]  # Shorter.
						if o1 != o2: next_shorter_relators.add((o1, o2))
		
		shorter_relators.update(new_shorter_relators)
		new_shorter_relators = next_shorter_relators
	
	shorter_relators.update(new_shorter_relators)
	
	return [x for (x, y) in shorter_relators]
	#######################
	
	# extended_relators = old_relators + [(letter+letter.swapcase(), '') for letter in alphabet]
	# RW = rewriting_system(order, extended_relators)
	# return [x for (x,y) in RW.find_new_relators(n, max_len) if len(x) > len(y)]

