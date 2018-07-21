
##### Required modules:
# Some custom modules.
from census_generation.options import options
from census_generation.census_generators import census_generator
from census_generation.fileio import pad_list

surface_name = 'S_1_2_5'
MCG_generators = 'aAbBcCxXyY'
arc_neighbours = {'x':{'c':['a', 'a']}, 'y':{'a':['c', 'c']}}
MCG_must_contain = []
MCG_automorphisms = [(None, 'cCbBaAyYxY')]

###-------------------------------------------------------------------------------------
# Load all of this information in.
def build_generator():
	return census_generator(MCG_generators, arc_neighbours, MCG_automorphisms, MCG_must_contain, options(surface_name))

if __name__ == '__main__':
	import sys
	G = build_generator()
	G.option.MULTIPROCESS_GROW = True
	G.option.MULTIPROCESS_LOAD = True
	G.option.MULTIPROCESS_THIN = True
	G.build_census(*pad_list(sys.argv[1:], 3, 0, int))