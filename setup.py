from setuptools import setup, find_packages, Extension

requirements = [
    'pandas',
    'numpy',
    'decorator'
]

core_FSM = Extension(
    name = 'bundler.extensions.c_FSM_core',
    sources = ['./bundler/extensions/c_FSM_core.cpp'],
    language='c++'
    )
core_matrix = Extension(
    name = 'bundler.extensions.c_matrix_core',
    sources = ['./bundler/extensions/c_matrix_core.cpp'],
    language='c++'
    )

core_automorph = Extension(
    name = 'bundler.extensions.c_automorph_core',
    sources = ['./bundler/extensions/c_automorph_core.cpp'],
    language='c++'
    )

setup(
    name='bundler',
    version='0.1.0',
    description='',
    author='Mark Bell',
    author_email='mcbell@illinois.edu',
    url='https://github.com/MarkCBell/bundles',
    packages=find_packages(),
    install_requires=requirements,
    ext_modules=[core_FSM, core_matrix, core_automorph],
    license='MIT License',
    zip_safe=False,
    keywords='bundler',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Education',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Scientific/Engineering :: Mathematics',
        ],
)
