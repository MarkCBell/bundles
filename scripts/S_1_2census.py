
##### Required modules:
# Some custom modules.
from bundler.options import options
from bundler.census_generators import census_generator
from bundler.fileio import pad_list

# The name of the surface we are using.
surface_name = 'S_1_2'

### Mapping class group of the surface:
# What the curves are called - this also determines what 'alphabetical order' is.
MCG_generators = 'aAbBcCxX'

# An optional dictionary of the arc neighbours. This is indexed by the names of arcs in the surface 
# and each consists of a dictionary indexed by the curves which intersect this arc exactly once. 
# This entry is then the list [LEFT_NEIGHBOUR, RIGHT_NEIGHBOUR].
arc_neighbours = {'x':{'c':['a', 'a']}}
# In this case, 'x' is the only arc, and 'c' is the only curve that meets it exactly once.

# Are there any elements of the MCG that MUST be present. For example are there any that if  
# missing instantly make a monodromy reducible?
MCG_must_contain = ['b', 'c', 'ax']

### Automorphisms of MCG:
MCG_automorphisms = [('x', 'cCbBaAxX')]
# If x is missing the you can translate the MCG generators to this.

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
