
from bundler.options import Options
from bundler.census_generators import CensusGenerator
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

def load_experiment(name, *args, **kwargs):
    with open('censuses.json') as sources:
        experiment = json.load(sources)[name]
    
    return CensusGenerator(
        experiment['generators'],
        experiment['arc_neighbours'],
        experiment['automorphisms'],
        experiment['MCG_must_contain'],
        Options(experiment['surface']),
        *args,
        **kwargs
        )

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Generate census')
    parser.add_argument('name', type=str,  help='name of experiment to load')
    parser.add_argument('depth', type=int, help='depth to generate to')
    parser.add_argument('--prebuilt', type=int, default=0, help='')
    parser.add_argument('--find', type=str, help='path to a file containing mondromies to find')
    args = parser.parse_args()
    
    if args.find is not None:
        manifolds = load_words_from_file(args.find)
        
        ACCEPTABLE_HOMOLOGY_ORDERS = set(reduce(mul, Manifold(name).homology().coefficients[:-1], 1) for name in manifolds)
        def word_filter(self, word):
            return self.homology_order(word) in ACCEPTABLE_HOMOLOGY_ORDERS
        
        ACCEPTABLE_VOLUMES = [float(Manifold(name).volume()) for name in manifolds]
        def manifold_filter(self, M):
            if not any(abs(M.volume() - v) <= self.option.VOLUME_ERROR for v in ACCEPTABLE_VOLUMES):
                return False
            return True
        kwargs = {'word_filter': word_filter, 'manifold_filter': manifold_filter}
    else:
        kwargs = dict()
    
    G = load_experiment(args.name, **kwargs)
    G.build_census(args.depth, args.prebuilt)
    
    if args.find is not None:
        find = pd.DataFrame({'name': manifolds, 'isom_sig': [Manifold(name).isometry_signature() for name in manifolds]})
        census = pd.read_csv(G.option.census_file, index_col='isom_sig')
        
        df = find.join(census, on='isom_sig')
        df.to_csv('matches.csv', index=False)
        print('%d / %d manifold(s) named.' % (df.word.count(), len(df)))

