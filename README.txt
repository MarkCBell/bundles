Scripts for generating various surface bundles over the circle using Twister, flipper, curver and SnapPy.

Results can be found in the `censuses` folder.
We provide monodromys as words in a generating set for the mapping class group of the surface.
In many cases this is the standard surface file that is included in Twister.
For example, as the word aBCx appears in the S_1_2 census this manifold can be built in SnapPy
by doing:
    >>> M = twister.Surface('S_1_2').bundle('aBCx')
or:
    >>> M = snappy.Manifold(flipper.load('S_1_2')('aBCx'))

Originally this project could build surface bundles where the fibre is a closed surface.
If you need access to this functionality checkout the tag: v0.1.0.
However, this should be used with caution.
In many cases SnapPy could not tell if two bundles were isometric and so although these lists are complete they likely contain duplicates.

To generate a new census, install dependencies and compile the packages extensions by running:
    $ pip install -r requirements.txt
    $ python setup.py build_ext --inplace

Then start one by doing, for example:
    $ python generate.py --name S_1_2 --depth 6

For more performance, also install one of the realalg extension (cypari, cypari2 or Sagemath):
    $ pip install cypari
