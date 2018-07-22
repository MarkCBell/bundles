
from bundler.options import options
from bundler.census_generators import census_generator
import json

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
    args = parser.parse_args()

    G = load_experiment(args.name)
    G.build_census(args.depth, args.prebuilt, args.skip)
