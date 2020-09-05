from setuptools import setup, Extension
from Cython.Build import cythonize

extensions = [
    Extension('bundler.extensions.FSM', ['./bundler/extensions/FSM.pyx']),
    Extension('bundler.extensions.automorphism', ['./bundler/extensions/automorphism.pyx']),
    Extension('bundler.extensions.ordering', ['./bundler/extensions/ordering.pyx']),
    ]

setup(
    ext_modules=cythonize(extensions, annotate=True),
)
