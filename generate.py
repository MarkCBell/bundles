
import argparse
from bundler.census_generator import CensusGenerator, Options

EXPERIMENTS = {
    "S_1_1": {
        "surface": "S_1_1",
        "generators": "aAbB",
        "MCG_must_contain": "aA^bB",
        "automorphisms": "aAbB|AaBb|bBaA|BbAa"
        },
    "S_1_2": {
        "surface": "S_1_2",
        "generators": "aAbBcCxX",
        "MCG_must_contain": "bB^cC^aAxX",
        "automorphisms": "aAbBcCxX|AaBbCcXx|xX:cCbBaAxX|xX:CcBbAaXx"
        },
    "S_1_2p": {
        "surface": "S_1_2",
        "generators": "aAbBcC",
        "MCG_must_contain": "bB^cC^aA",
        "automorphisms": "aAbBcC|AaBbCc|cCbBaA|CcBbAa"
        },
    "S_1_3": {
        "surface": "S_1_3",
        "generators": "aAbBcCdDxXyY",
        "MCG_must_contain": "bB^cCdD^aAxXyY",
        "automorphisms": ""
        },
    "S_2_1": {
        "surface": "S_2_1",
        "generators": "aAbBcCdDeEfF",
        "MCG_must_contain": "aA^bB^cC^dDeEfF",
        "automorphisms": "aAbBcCdDeEfF|AaBbCcDdEeFf|aAbBcCeEdDfF|AaBbCcEeDdFf|eE:cCbBaAfFeEdD|eE:CcBbAaFfEeDd|eE:cCbBaAfFeEdD|eE:CcBbAaFfEeDd|eE:cCbBaAfFdDeE|eE:CcBbAaFfDdEe"
        },
    "S_3_1": {
        "surface": "S_3_1",
        "generators": "aAbBcCdDeEfFgGhH",
        "MCG_must_contain": "aA^bB^cC^dD^eE^fFgGhH",
        "automorphisms": "aAbBcCdDeEfFgGhH|AaBbCcDdEeFfGgHh|hH:aAbBcCdDeEgGfFhH|hH:AaBbCcDdEeGgFfHh"
        },
    "S_4_1": {
        "surface": "S_4_1",
        "generators": "aAbBcCdDeEfFgGhHiIjJ",
        "MCG_must_contain": "aA^bB^cC^dD^eE^fF^gG^hHiIjJ",
        "automorphisms": "aAbBcCdDeEfFgGhHiIjJ|AaBbCcDdEeFfGgHhIiJj|jJ:aAbBcCdDeEfFgGiIhHjJ|jJ:AaBbCcDdEeFfGgIiHhJj"
        },
    "S_5_1": {
        "surface": "S_5_1",
        "generators": "aAbBcCdDeEfFgGhHiIjJkKlL",
        "MCG_must_contain": "aA^bB^cC^dD^eE^fF^gG^hHiI^jJkKlL",
        "automorphisms": "aAbBcCdDeEfFgGhHiIjJkKlL|AaBbCcDdEeFfGgHhIiJjKkLl|lL:aAbBcCdDeEfFgGhHiIkKjJlL|lL:AaBbCcDdEeFfGgHhIiKkJjLl"
        }
}

def setup(**kwargs):
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('name', type=str, help='name of experiment to load')
    parser.add_argument('depth', type=int, help='depth to generate to')
    parser.add_argument('--prebuilt', '-p', type=int, default=0, help='The amount of steps that have already been completed')
    for key, value in vars(Options()).items():
        parser.add_argument('--{}'.format(key), default=value, type=value.__class__, help=' ')
    args = parser.parse_args()
    options = Options(**vars(args))
    
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

