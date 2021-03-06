
from functools import reduce
from operator import mul
from snappy import Manifold
from sympy import Matrix
import argparse
import numpy as np

import generate

def presetup():
    parser = argparse.ArgumentParser()
    parser.add_argument('--find', type=str, help='name of a snappy manifold to find')
    parser.add_argument('--finds', type=str, help='path to a file containing mondromies to find')
    args, _ = parser.parse_known_args()
    
    if args.find:
        manifolds = [args.find]
    elif args.finds:
        with open(args.find, 'r') as source:
            manifolds = [line for line in source]
    else:
        parser.error('at least one of --find and --finds is required')
    
    ACCEPTABLE_HOMOLOGY_TORSIONS = set(reduce(mul, Manifold(name).homology().coefficients[:-1], 1) for name in manifolds)
    def word_filter(self, word):
        A = np.linalg.multi_dot([self.curver_action[letter].homology_matrix() for letter in word[::-1]])
        M = Matrix(A - np.eye(A.shape[0], dtype=object))
        homology_torsion = int(abs(M.det()))
        return homology_torsion in ACCEPTABLE_HOMOLOGY_ORDERS
    
    ACCEPTABLE_ISOM_SIG = set(Manifold(name).isometry_signature() for name in manifolds)
    def manifold_filter(self, M):
        return M.isometry_signature() in ACCEPTABLE_ISOM_SIG
    
    return {'word_filter': word_filter, 'manifold_filter': manifold_filter}

if __name__ == '__main__':
    generate.setup(**presetup())

