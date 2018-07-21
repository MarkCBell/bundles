
##### Required modules:
# Some standard modules:
from __future__ import print_function
import sys
import os
from functools import reduce
from operator import mul

# Some custom modules:
from census_generation.fileio import load_words_from_file, print_table_to_file, clean_files
from census_generation.fileio import pad_list, line_count, chunk
from snappy import Manifold

if __name__ == '__main__':
	S = __import__(sys.argv[1][:-3])
	G = S.build_generator()
	
	G.option.MULTIPROCESS_GROW = True
	G.option.MULTIPROCESS_LOAD = True
	G.option.MULTIPROCESS_THIN = True
	
	# Extract the target manifold volumes and homology.
	to_find_file = os.path.join(G.option.census_dir, 'to_find.txt')
	manifolds = load_words_from_file(to_find_file)
	G.option.ACCEPTABLE_HOMOLOGY_ORDERS = [reduce(mul, Manifold(name).homology().coefficients[:-1], 1) for name in manifolds]
	G.option.ACCEPTABLE_VOLUMES = [float(Manifold(name).volume()) for name in manifolds]
	G.option.tidy()
	
	G.build_census(*pad_list(sys.argv[2:], 3, 0, int))
	
	# -----------------------------------------------------------------------------------------------------------------------------------------------
	
	# Caution: This wont work if manifolds is a really long list!
	manifold_table = [[name, Manifold(name), Manifold(name).volume(), Manifold(name).homology()] for name in manifolds]
	results_file = os.path.join(G.option.census_dir, 'matches.txt')
	clean_files(results_file)
	
	print('%d words to check.' % line_count(G.option.census_file))
	word_blocks = chunk(load_words_from_file(G.option.census_file), G.option.CHUNKSIZE_LOAD)
	
	c = 0
	for i in range(len(word_blocks)):
		print('Loading block %d / %d.' % (i+1, len(word_blocks)))
		table, problem_words, filtered_words = G.table_generator.convert_words_table(word_blocks[i])
		table_width = len(table[0])
		
		print('Naming manifolds')
		for index, row in enumerate(manifold_table):
			if G.option.SHOW_PROGRESS: print('\rNaming: %d / %d.' % (index, len(manifold_table)), end='')
			i = G.table_generator.check_existance_table(table, row[1])
			if i != -1:
				row.append(table[i][0])
				c += 1
		
		for row in manifold_table:
			if len(row) == table_width: row.append('---')
		
		print_table_to_file(manifold_table, results_file, 'a')
		if G.option.SHOW_PROGRESS: print('\rNaming: DONE          ')
		print('%d / %d manifolds named.' % (c, len(manifold_table)))
