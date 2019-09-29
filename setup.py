from setuptools import setup, find_packages
from Cython.Build import cythonize

requirements = [
    'contexttimer',
    'curver',
    'decorator',
    'flipper',
    'numpy',
    'pandas',
    'sympy',
]

setup(
    name='bundler',
    version='0.1.0',
    description='',
    author='Mark Bell',
    author_email='mcbell@illinois.edu',
    url='https://github.com/MarkCBell/bundles',
    packages=find_packages(),
    install_requires=requirements,
    ext_modules=cythonize([
        './bundler/extensions/FSM.pyx',
        './bundler/extensions/automorphism.pyx',
        './bundler/extensions/ordering.pyx',
        ], annotate=True),
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
