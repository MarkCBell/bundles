
##### Required modules:
# Some custom modules.
from bundler.options import options
from bundler.census_generators import census_generator
from bundler.fileio import pad_list

surface_name = 'S_3_1'
MCG_generators = 'aAbBcCdDeEfFgGhH'
arc_neighbours = {}
MCG_must_contain = ['a', 'b', 'c', 'd', 'e', 'fgh']
MCG_automorphisms = [('h', 'aAbBcCdDeEgGfFhH')]

###-------------------------------------------------------------------------------------
# Load all of this information in.
def build_generator():
	return census_generator(MCG_generators, arc_neighbours, MCG_automorphisms, MCG_must_contain, options(surface_name))

if __name__ == '__main__':
	import sys
	G = build_generator()
	G.build_census(*pad_list(sys.argv[1:], 3, 0, int))
