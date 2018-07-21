from distutils.core import setup, Extension, Command

core = Extension(
	name = 'c_automorph.c_automorph_core',
	sources = ['./kernel/c_automorph_core.cpp'],
	language='c++'
	)

setup(
	name='c_automorph',
	version='1.0',
	description='',
	author='Mark Bell',
	author_email='M.C.Bell@warwick.ac.uk',
	url='http://www.surfacebundles.wordpress.com/',
	packages=['c_automorph'],
	package_dir={'c_automorph':'kernel'},
	ext_modules=[core],
	# cmdclass = {'test': TestCommand}
	)
