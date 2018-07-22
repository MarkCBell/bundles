##### Required modules:
from __future__ import print_function
import os
from random import randint

import bundler.ordering as ordering

# Solution types:
Abbrev = {'not attempted' : 'not attempted',
			'all tetrahedra positively oriented' : 'pos',
			'contains negatively oriented tetrahedra' : 'neg',
			'contains flat tetrahedra' : 'flat',
			'contains degenerate tetrahedra' : 'deg',
			'unrecognized solution type' : 'unrec',
			'no solution found' : 'none found'}

get_volume = lambda m: m[2]

### Is there a better way?
def isometry_test(M, N):
	for i in range(1):
		if M.is_isometric_to(N):
			return True
		# M.randomize()
		# N.randomize()
	
	return False

class table_generator:
	def __init__(self, MCG_generators, manifold_filter, option):
		self.MCG_generators = MCG_generators
		self.MCG_ordering = ordering.short_lex(MCG_generators)
		self.manifold_filter = manifold_filter
		self.option = option
	
	def build_manifold(self, word):
		''' Builds a manifold in twister corresponding to a particular word. '''
		
		M = self.option.BASE_SURFACE.bundle(monodromy='*'.join(word))
		
		for i in self.option.MAX_RANDOMIZE_RANGE:  # Try, at most MAX_RANDOMIZE times, to find a solution for M.
			if Abbrev[M.solution_type()] == 'pos': break
			M.randomize()  # There needs to be a better way to do this.
		
		return M
	
	def convert_words_table(self, words):
		''' Accepts a list of words and loads their statistics into a table. '''
		if self.option.SHOW_PROGRESS: print('Loading table.')
		
		table, problem_words, filtered_words = [], [], []
		for index, word in enumerate(words):
			if self.option.SHOW_PROGRESS and not randint(0,self.option.PROGRESS_RATE_LOAD): print('\rLoading: %d / %d.     ' % (index+1, len(words)), end='')
			
			M = self.build_manifold(word)
			if Abbrev[M.solution_type()] != 'pos':
				problem_words.append(word)
			elif self.option.ACCEPTABLE_VOLUMES and all(abs(M.volume() - v) > self.option.VOLUME_ERROR for v in self.option.ACCEPTABLE_VOLUMES):
				filtered_words.append(word)
			elif not self.manifold_filter(self, M):
				filtered_words.append(word)
			else:
				table.append([word, M, float(M.volume()), str(M.homology())])  # Could put more invariants here.
		
		table.sort(key=lambda row: round(row[2], self.option.VOLUME_ROUND))
		if self.option.SHOW_PROGRESS: print('\rLoading: DONE           ')
		
		return table, problem_words, filtered_words
	
	def remove_duplicates_table(self, table):
		''' None's out rows of the table to leave one representative of each isotopy class.
		Assumes that each line of the table given to it is in the format
			[word, manifold_object, volume, homology...] '''
		if self.option.SHOW_PROGRESS: print('Thinning table.')
		
		if len(table) <= 1: return
		
		table.sort(key=get_volume)
		
		for i in range(len(table)):
			if self.option.SHOW_PROGRESS and not randint(0,self.option.PROGRESS_RATE_THIN): print('\rThinning: %d / %d.     ' % (i, len(table)), end='')
			RI = table[i]
			
			for j in range(i-1,-1,-1):  # Quadratic here, but this is usually small (< 10). - Ha! In the S_1_2 13 census volume buckets were ~2900.
				RJ = table[j]
				if RJ is None: continue
				
				if abs(RI[2] - RJ[2]) > self.option.VOLUME_ERROR: break  # Skip if the hyp. volumes aren't the same.
				if RI[3] != RJ[3]: continue  # Skip if the homologies aren't the same.
				# if abs(table[i][4] - table[j][4]) > self.option.CHERN_SIMONS_ERROR: continue
				# for k in range(4,len(i)):  # Extra invarients.
					# if i[k] != j[k]: continue  # (within error.)
				
				try:
					if isometry_test(RI[1], RJ[1]):
						table[j if self.MCG_ordering.ordered(RI[0], RJ[0]) else i] = None
						break
				except:
					if self.option.SHOW_WARNINGS: print('%s ?~ %s' % (RI[0], RJ[0]))
		
		table.sort(key=lambda row: (0,) if row is None else (round(row[2], self.option.VOLUME_ROUND), len(row[0]), row[0].translate(self.MCG_ordering.translate_rule)))
		
		if self.option.SHOW_PROGRESS: print('\rThinning: DONE           ')
		return
	
	def check_uniqueness_table(self, table):
		''' Checks that the entries of table are unique. '''
		table = [row for row in table if row is not None]
		table.sort(key=get_volume)
		
		good = True
		for i in range(len(table)):
			if self.option.SHOW_PROGRESS and not randint(0,self.option.PROGRESS_RATE_VALIDATE): print('\rChecking: %d / %d.     ' % (i, len(table)), end='')
			for j in range(i-1, -1, -1): # This is equivalent to range(0, i)[::-1]:
				if abs(table[i][2] - table[j][2]) > self.option.VOLUME_ERROR: break
				if table[i][3] != table[j][3]: continue  # Skip if the homologies aren't the same.
				# if abs(table[i][4] - table[j][4]) > self.option.CHERN_SIMONS_ERROR: continue
				#for k in range(4,len(i)):  # Extra invariants
				#	if i[k] != j[k] (within error): continue
				
				try:
					if table[i][1].is_isometric_to(table[j][1]):
						if self.option.SHOW_ERRORS: print('%s ~ %s' % (table[i][0], table[j][0]))
						good = False
				except:
					if self.option.SHOW_WARNINGS: print('Error with %s & %s' % (table[i][0], table[j][0]))
					good = False
		
		if self.option.SHOW_PROGRESS: print('\rChecking: DONE           ')
		return good
	
	def check_existance_table(self, table, M):
		''' Checks that the manifold M appears in table. '''
		table.sort(key=get_volume)
		volume = M.volume()
		
		volume_low = volume - self.option.VOLUME_ERROR
		volume_high = volume + self.option.VOLUME_ERROR
		
		# Use a binary search to find a small range to check quickly.
		low_x, low_y = 0, len(table)
		high_x, high_y = 0, len(table)
		
		while abs(low_x - low_y) > 2:
			mid = int((low_x + low_y) / 2)
			if table[mid][2] < volume_low:
				low_x = mid
			elif table[mid][2] > volume_low:
				low_y = mid
		
		while abs(high_x - high_y) > 2:
			mid = int((high_x + high_y) / 2)
			if table[mid][2] < volume_high:
				high_x = mid
			elif table[mid][2] > volume_high:
				high_y = mid
		
		for i in range(low_x, high_y):
			try:
				if table[i][1].is_isometric_to(M): return i
			except:
				print('Error with %s' % table[i][0])
		
		return -1

