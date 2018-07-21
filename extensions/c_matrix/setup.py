from distutils.core import setup, Extension, Command

core = Extension(
	name = 'c_matrix.c_matrix_core',
	sources = ['./kernel/c_matrix_core.cpp'],
	language='c++'
	)

setup(
	name='c_matrix',
	version='1.0',
	description='',
	author='Mark Bell',
	author_email='M.C.Bell@warwick.ac.uk',
	url='http://www.surfacebundles.wordpress.com/',
	packages=['c_matrix'],
	package_dir={'c_matrix':'kernel'},
	ext_modules=[core],
	# cmdclass = {'test': TestCommand}
	)
