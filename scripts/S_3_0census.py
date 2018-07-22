
##### Required modules:
# Some custom modules.
from census_generation.options import options
from census_generation.census_generators import census_generator
from census_generation.fileio import pad_list
from c_matrix import matrix_as_string

surface_name = 'S_3_0'
MCG_generators = 'aAbBcCdDeEfFgg'
arc_neighbours = {}
MCG_must_contain = ['a', 'b', 'c', 'd', 'e', 'fg']
MCG_automorphisms = [('f', 'eEdDcCbBaAfFgG')]

###-------------------------------------------------------------------------------------
# Load all of this information in.
def build_generator():
	return census_generator(MCG_generators, arc_neighbours, MCG_automorphisms, MCG_must_contain, options(surface_name))

if __name__ == '__main__':
	import sys
	G = build_generator()
	G.option.ACCEPTABLE_HOMOLOGY_ORDERS = [1]
	G.option.tidy()
	G.build_census(*pad_list(sys.argv[1:], 3, 0, int))
