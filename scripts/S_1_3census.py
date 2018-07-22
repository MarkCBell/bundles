
##### Required modules:
# Some custom modules.
from bundler.options import options
from bundler.census_generators import census_generator
from bundler.fileio import pad_list

# The name of the surface we are using.
surface_name = 'S_1_3'

### Mapping class group of the surface:
MCG_generators = 'aAbBcCdDxXyY'

arc_neighbours = {'x':{'c':['a', 'd']}, 'y':{'d':['c', 'a']}}
MCG_must_contain = ['b', 'cd', 'axy']

### Automorphisms of MCG:
# MCG_automorphisms = [('', 'aAbBdDcCyYxX')]
MCG_automorphisms = []

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
