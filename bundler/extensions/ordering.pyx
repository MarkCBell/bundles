from string import ascii_lowercase

cdef class ShortLex:
    ''' This class acts as an ordering system for the ordering 'short lexicographical'
    with respect to the ordered alphabet provided at initialisation. '''
    cdef str alphabet
    cdef public dict translate_rule
    
    def __init__(self, str alphabet):
        if len(alphabet) > len(ascii_lowercase):
            raise IndexError('Alphabet requested is too large.')
        
        self.alphabet = alphabet
        self.translate_rule = str.maketrans(self.alphabet, ascii_lowercase[:len(alphabet)])
    
    def translate(self, str word):
        return word.translate(self.translate_rule)
    
    def __call__(self, str word):
        return (len(word), self.translate(word))
    
    def cmp(self, str A, str B):
        ''' Return True iff A is strictly before B. '''
        return self(A) < self(B)
    
    def first(self, words):
        ''' Return the alphabetically first word in words. '''
        return min(words, key=self)

