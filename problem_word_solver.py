##### Required modules:
from __future__ import print_function
from time import time
import os

from census_generation.Aut_Fn import generate_FSM_info
from census_generation.fileio import load_words_from_file, print_words_to_file
#--------------------------------------------------------------

def verify_problem_words(S, n=5):
	''' Tries to find a solution to all the problem words in the list words
	by checking for reducibility and periodicity in that order. '''
	
	G = S.build_generator()
	WG = G.word_generator
	
	print('Rebuilding machine')
	start = time()
	Advanced_Loop_invariant_FSM = generate_FSM_info(WG.MCG_generators, WG.loop_invariant_FSM_seed, n, WG.fundamental_group_action)
	# Advanced_Loop_invariant_FSM.raise_power(2)
	
	words = load_words_from_file(G.option.problem_file)
	
	output_words = []
	solutions = ['Solutions:']
	
	for index, word in enumerate(words):
		print('\rChecking: %d / %d.' % (index, len(words)), end='')
		
		if Advanced_Loop_invariant_FSM.has_cycle(word[::-1] * 6):  # We also check for up to the 6th power.
			solutions.append(word + ' is reducible.')
			print('%s is reducible.' % word)
		elif not WG.valid_word(word):  # Is word really a valid word? Previously max_tree_size != 0.
			solutions.append(word + ' is not lex first in its class.')
			print('%s is not lex first in its class.' % word)
		else:
			output_words.append(word)
			print('%s - No Solution Found!' % word)
	
	print('\nChecking: DONE')
	print('Running time: %fs.' % (time() - start))
	print('%i solved.' % (len(words) - len(output_words)))
	print('%i words remain.' % len(output_words))
	# print(output_words)
	
	solutions.append('')
	solutions.append('')
	solutions.append('Running time: %fs.' % (time() - start))
	solutions.append('%i words remain.' % len(output_words))
	solutions.extend(output_words)
	
	print_words_to_file(solutions, os.path.join(G.option.census_dir, 'solutions.txt'))
	
	# Advanced_Loop_invariant_FSM.print_interesting_cycle_buckets()
	
	return output_words

if __name__ == '__main__':
	import sys
	verify_problem_words(__import__(sys.argv[1][:-3]), int(sys.argv[2]))
	print('DONE')
