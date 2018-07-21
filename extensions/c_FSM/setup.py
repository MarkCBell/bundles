from distutils.core import setup, Extension, Command

core = Extension(
	name = 'c_FSM.c_FSM_core',
	sources = ['./kernel/c_FSM_core.cpp'],
	language='c++'
	)

setup(
	name='c_FSM',
	version='1.0',
	description='',
	author='Mark Bell',
	author_email='M.C.Bell@warwick.ac.uk',
	url='http://www.surfacebundles.wordpress.com/',
	packages=['c_FSM'],
	package_dir={'c_FSM':'kernel'},
	ext_modules=[core],
	# cmdclass = {'test': TestCommand}
	)
