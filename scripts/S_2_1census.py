
##### Required modules:
# Some custom modules.
from bundler.options import options
from bundler.census_generators import census_generator
from bundler.fileio import pad_list

surface_name = 'S_2_1'
MCG_generators = 'aAbBcCdDeEfF'
arc_neighbours = {}
MCG_must_contain = ['a', 'b', 'c', 'def']
MCG_automorphisms = [(None, 'aAbBcCeEdDfF'), ('e', 'cCbBaAfFeEdD'), ('e', 'cCbBaAfFeEdD'), ('e', 'cCbBaAfFdDeE')] 

###-------------------------------------------------------------------------------------
# Load all of this information in.
def build_generator():
	return census_generator(MCG_generators, arc_neighbours, MCG_automorphisms, MCG_must_contain, options(surface_name))

if __name__ == '__main__':
	import sys
	G = build_generator()
	G.build_census(*pad_list(sys.argv[1:], 3, 0, int))
