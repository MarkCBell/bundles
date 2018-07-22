from distutils.core import setup, Extension, Command

core_FSM = Extension(
	name = 'bundle_ext.c_FSM_core',
	sources = ['./kernel/c_FSM_core.cpp'],
	language='c++'
	)
core_matrix = Extension(
	name = 'bundle_ext.c_matrix_core',
	sources = ['./kernel/c_matrix_core.cpp'],
	language='c++'
	)

core_automorph = Extension(
	name = 'bundle_ext.c_automorph_core',
	sources = ['./kernel/c_automorph_core.cpp'],
	language='c++'
	)

setup(
	name='bundle_ext',
	version='1.0',
	description='',
	author='Mark Bell',
	author_email='M.C.Bell@warwick.ac.uk',
	url='http://www.surfacebundles.wordpress.com/',
	packages=['bundle_ext'],
	package_dir={'bundle_ext':'kernel'},
	ext_modules=[core_FSM, core_matrix, core_automorph],
	)
