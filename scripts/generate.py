
import argparse
import bundler.census_generators
import json
import os

def setup(**kwargs):
    parser = argparse.ArgumentParser()
    parser.add_argument('--name', required=True, type=str,  help='name of experiment to load')
    parser.add_argument('--depth', required=True, type=int, help='depth to generate to')
    parser.add_argument('--prebuilt', type=int, default=0, help='')
    args, _ = parser.parse_known_args()
    
    options_parser = argparse.ArgumentParser()
    for key, value in vars(bundler.census_generators.Options()).items():
        options_parser.add_argument('--{}'.format(key), default=value, type=value.__class__)
    options_args, _ = options_parser.parse_known_args()
    options = bundler.census_generators.Options(**vars(options_args))
    
    with open(os.path.join(os.path.dirname(__file__), 'censuses.json')) as sources:
        experiment = json.load(sources)[args.name]
    
    G = bundler.CensusGenerator(
        experiment['surface'],
        experiment['generators'],
        experiment['automorphisms'],
        experiment['MCG_must_contain'],
        **kwargs,
        options=options,
        )
    G.build_census(args.depth, args.prebuilt)

if __name__ == '__main__':
    setup()

