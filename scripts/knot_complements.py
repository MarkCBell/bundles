from math import gcd
import argparse

import generate

def presetup():
    def word_filter(self, word):
        return self.homology_order(word) == 1
    
    def manifold_filter(self, M):
        M.set_peripheral_curves('shortest')
        C = M.cusp_neighborhood()
        C.set_displacement(C.reach())
        A, B = C.translations()
        
        if A.imag == 0 or B.real == 0: A, B = B, A
        
        p = int(6 / B.real) + 1
        q = int(6 / A.imag) + 1
        r = int((p*B.imag) / A.imag) + 1
        
        def trivial_fill(i, j):
            N = M.copy()
            N.dehn_fill((i, j))
            return len(N.fundamental_group().generators()) == 0
        
        return any(trivial_fill(i, j) for i in range(-p, p) for j in range(-r, q+r) if gcd(i, j) != 1 and abs(i*A + j*B) <= 6)
    
    return {'word_filter': word_filter, 'manifold_filter': manifold_filter}

if __name__ == '__main__':
    generate.setup(**presetup())

