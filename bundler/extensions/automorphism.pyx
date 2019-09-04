
cdef is_cyclic_ordered(str A, str B):
    return all(A <= B[i:] + B[:i] for i in range(len(A)))

cdef class Automorph:
    cdef bint symmetric_generators
    cdef str alphabet
    cdef dict swapcase
    cdef list always_automorphisms
    cdef list missing_automorphisms
    
    def __init__(self, bint symmetric_generators, str alphabet, str swapcase, list always_automorphisms, list missing_automorphisms):
        cdef str missing, auto
        
        self.symmetric_generators = symmetric_generators
        self.alphabet = alphabet
        self.swapcase = str.maketrans(self.alphabet, swapcase)
        self.always_automorphisms = [str.maketrans(self.alphabet, auto) for auto in always_automorphisms]
        self.missing_automorphisms = [(missing, str.maketrans(self.alphabet, auto)) for missing, auto in missing_automorphisms]
    
    def before_automorphs(self, str word, str next_word, bint prefix=False):
        cdef str missing
        cdef set next_word_letters
        cdef str letter
        cdef str trans
        
        # Trivial automorphism.
        if not self.check_automorph(word, next_word):
            return False
        
        if any(not self.check_automorph(word, next_word.translate(trans)) for trans in self.always_automorphisms):
            return False
        
        if not prefix:
            next_word_letters = set(x for letter in next_word for x in [letter, letter.translate(self.swapcase)])
            if any(all(letter not in next_word_letters for letter in missing) and not self.check_automorph(word, next_word.translate(trans)) for missing, trans in self.missing_automorphisms):
                return False
        
        return True
    
    cdef check_automorph(self, str word, str next_word):
        # Return whether word is before all cyclic permutations of all automorphs of next_word.
        if not is_cyclic_ordered(word, next_word):
            return False
        
        if self.symmetric_generators and not is_cyclic_ordered(word, next_word[::-1]):
            return False
        
        cdef str next_word_swap = next_word.translate(self.swapcase)
        if self.symmetric_generators and not is_cyclic_ordered(word, next_word_swap):
            return False
        
        if not is_cyclic_ordered(word, next_word_swap[::-1]):
            return False
        
        return True

