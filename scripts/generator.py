
from bundler.options import options
from bundler.census_generators import census_generator
from bundler.fileio import load_words_from_file, print_table_to_file, clean_files
from bundler.fileio import line_count, chunk
import json
from snappy import Manifold
from operator import mul
import os
try:
    from functools import reduce
except ImportError:
    pass

def load_experiment(name):
    with open('censuses.json') as sources:
        experiment = json.load(sources)[name]
    
    return census_generator(
        experiment['generators'],
        experiment['arc_neighbours'],
        experiment['automorphisms'],
        experiment['MCG_must_contain'],
        options(experiment['surface'])
        )

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Generate census')
    parser.add_argument('name', type=str,  help='name of experiment to load')
    parser.add_argument('depth', type=int, help='depth to generate to')
    parser.add_argument('--prebuilt', type=int, default=0, help='')
    parser.add_argument('--skip', type=int, default=0, help='')
    parser.add_argument('--find', type=str, help='')
    args = parser.parse_args()
    
    G = load_experiment(args.name)
    
    if args.find is not None:
        manifolds = load_words_from_file(args.find)
        G.option.ACCEPTABLE_HOMOLOGY_ORDERS = [reduce(mul, Manifold(name).homology().coefficients[:-1], 1) for name in manifolds]
        G.option.ACCEPTABLE_VOLUMES = [float(Manifold(name).volume()) for name in manifolds]
        G.option.tidy()
    
    G.build_census(args.depth, args.prebuilt, args.skip)
    
    if args.find is not None:
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

