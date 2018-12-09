Scripts for generating various surface bundles over the circle using Twister
and SnapPy.

Results can be found in the `censuses` folder.  We provide monodromys as words
in a generating set for the mapping class group of the surface. In many cases
this is the standard surface file that is included in Twister.  For example, as
the word aBCx appears in the S_1_2 census this manifold can be built in SnapPy
by doing:
    >>> M = twister.Surface('S_1_2').bundle('aBCx')

The censuses in which the fibre is a closed surface should be used with
caution. In many cases SnapPy could not tell if two bundles were isometric and
so although these lists are complete they likely contain duplicates.

To generate a new census, compile the packages extensions and install it by
running:
    $ pip install .
or:
    $ python setup.py install
Then start one by doing, for example:
    $ python scripts/generators.py S_1_2 6
