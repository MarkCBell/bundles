
import argparse
from bundler.census_generator import CensusGenerator, Options

EXPERIMENTS = {
    "S_1_1": {
        "surface": "S_1_1",
        "generators": "aAbB",
        "MCG_must_contain": "aA^bB",
        "automorphisms": [["", "bBaA"]]
        },
    "S_1_2": {
        "surface": "S_1_2",
        "generators": "aAbBcCxX",
        "MCG_must_contain": "bB^cC^aAxX",
        "automorphisms": [["x", "cCbBaAxX"]]
        },
    "S_1_2p": {
        "surface": "S_1_2",
        "generators": "aAbBcC",
        "MCG_must_contain": "bB^cC^aA",
        "automorphisms": [["", "cCbBaA"]]
        },
    "S_1_3": {
        "surface": "S_1_3",
        "generators": "aAbBcCdDxXyY",
        "MCG_must_contain": "bB^cCdD^aAxXyY",
        "automorphisms": []
        },
    "S_2_0": {
        "surface": "S_2",
        "generators": "aAbBcCdDeE",
        "MCG_must_contain": "bB^cC^dD^aAeE",
        "automorphisms": [["", "eEdDcCbBaA"]]
        },
    "S_2_1": {
        "surface": "S_2_1",
        "generators": "aAbBcCdDeEfF",
        "MCG_must_contain": "aA^bB^cC^dDeEfF",
        "automorphisms": [["", "aAbBcCeEdDfF"], ["e", "cCbBaAfFeEdD"], ["e", "cCbBaAfFeEdD"], ["e", "cCbBaAfFdDeE"]]
        },
    "S_3_0": {
        "surface": "S_3_0",
        "generators": "aAbBcCdDeEfFgg",
        "MCG_must_contain": "aA^bB^cC^dD^eE^fFgG",
        "automorphisms": [["f", "eEdDcCbBaAfFgG"]]
        },
    "S_3_1": {
        "surface": "S_3_1",
        "generators": "aAbBcCdDeEfFgGhH",
        "MCG_must_contain": "aA^bB^cC^dD^eE^fFgGhH",
        "automorphisms": [["h", "aAbBcCdDeEgGfFhH"]]
        },
    "S_4_1": {
        "surface": "S_4_1",
        "generators": "aAbBcCdDeEfFgGhHiIjJ",
        "MCG_must_contain": "aA^bB^cC^dD^eE^fF^gG^hHiIjJ",
        "automorphisms": [["j", "aAbBcCdDeEfFgGiIhHjJ"]]
        },
    "S_5_1": {
        "surface": "S_5_1",
        "generators": "aAbBcCdDeEfFgGhHiIjJkKlL",
        "MCG_must_contain": "aA^bB^cC^dD^eE^fF^gG^hHiI^jJkKlL",
        "automorphisms": [["l", "aAbBcCdDeEfFgGhHiIkKjJlL"]]
        }
}

def setup(**kwargs):
    parser = argparse.ArgumentParser()
    parser.add_argument('--name', '-n', required=True, type=str, help='name of experiment to load')
    parser.add_argument('--depth', '-d', required=True, type=int, help='depth to generate to')
    parser.add_argument('--prebuilt', '-p', type=int, default=0, help='')
    args, _ = parser.parse_known_args()
    
    options_parser = argparse.ArgumentParser()
    for key, value in vars(Options()).items():
        options_parser.add_argument('--{}'.format(key), default=value, type=value.__class__)
    options_args, _ = options_parser.parse_known_args()
    options = Options(**vars(options_args))
    
    experiment = EXPERIMENTS[args.name]
    G = CensusGenerator(
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

