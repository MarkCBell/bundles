
cdef is_cyclic_ordered(tuple A, tuple B, bint prefix):
    ''' Return whether A is <= all cyclic perumtations of B.
    
    Equivalent to:
        return all(A <= B[i:] + B[:i] for i in range(len(A))) '''
    
    cdef int i, j, k, l = len(A)
    for k in range(l):
        j = k
        for i in range(l):
            j += 1
            if j >= l:
                if prefix:
                    return True
                else:
                    j = 0
            if A[i] < B[j]:
                break
            elif A[i] > B[j]:
                return False
    
    return True

cdef class Automorph:
    cdef list alphabet
    cdef list inverse
    cdef list automorphisms
    cdef int stop
    
    def __init__(self, list alphabet, list inverse, list automorphisms):
        cdef list missing, auto
        self.alphabet = alphabet
        self.stop = len(self.alphabet)
        self.inverse = inverse + [self.stop]
        self.automorphisms = [(missing, auto + [self.stop]) for missing, auto in automorphisms]
    
    def before_automorphs(self, tuple word, tuple next_word, bint prefix=False):
        # Return whether word is before all cyclic permutations of all automorphs of next_word and next_word^-1.
        cdef tuple other
        cdef tuple next_word_inverse = tuple(self.inverse[letter] for letter in next_word[::-1])
        for other in [next_word, next_word_inverse]:
            for missing, automorphism in self.automorphisms:
                if not (missing and prefix) and all(letter not in next_word for letter in missing) and not is_cyclic_ordered(word, tuple(automorphism[letter] for letter in other), prefix):
                    return False
        
        return True

