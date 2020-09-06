
cdef is_cyclic_ordered(str A, str B):
    return all(A <= B[i:] + B[:i] for i in range(len(A)))

cdef class Automorph:
    cdef str alphabet
    cdef dict swapcase
    cdef list automorphisms
    
    def __init__(self, str alphabet, str swapcase, list automorphisms):
        cdef str missing, auto
        self.alphabet = alphabet
        self.swapcase = str.maketrans(self.alphabet, swapcase)
        self.automorphisms = [(missing, str.maketrans(self.alphabet, auto)) for missing, auto in automorphisms]
    
    def before_automorphs(self, str word, str next_word, bint prefix=False):
        return not any(
            (not missing or (not prefix and all(letter not in next_word for letter in missing))) \
                and not self.check_automorph(word, next_word.translate(automorphism))
            for missing, automorphism in self.automorphisms)
    
    cdef check_automorph(self, str word, str next_word):
        # Return whether word is before all cyclic permutations of all automorphs of next_word.
        if not is_cyclic_ordered(word, next_word):
            return False
        
        cdef str next_word_swap = next_word.translate(self.swapcase)
        if not is_cyclic_ordered(word, next_word_swap[::-1]):
            return False
        
        return True

