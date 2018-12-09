
from bundler.options import options
from bundler.census_generators import census_generator
from bundler.fileio import load_words_from_file
import json
from operator import mul
import os
try:
    from functools import reduce
except ImportError:
    pass
import pandas as pd
from snappy import Manifold

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
    parser.add_argument('--find', type=str, help='path to a file containing mondromies to find')
    args = parser.parse_args()
    
    G = load_experiment(args.name)
    
    if args.find is not None:
        manifolds = load_words_from_file(args.find)
        G.option.ACCEPTABLE_HOMOLOGY_ORDERS = [reduce(mul, Manifold(name).homology().coefficients[:-1], 1) for name in manifolds]
        G.option.ACCEPTABLE_VOLUMES = [float(Manifold(name).volume()) for name in manifolds]
        G.option.tidy()
    
    G.build_census(args.depth, args.prebuilt)
    
    if args.find is not None:
        find = pd.DataFrame({'name': manifolds, 'isom_sig': [Manifold(name).isometry_signature() for name in manifolds]})
        census = pd.read_csv(G.option.census_file, index_col='isom_sig')
        
        df = find.join(census, on='isom_sig')
        df.to_csv('matches.csv', index=False)
        print('%d / %d manifold(s) named.' % (df.word.count(), len(df)))

