
''' This module contains ordering system classes. Eventually this will / should
contain many different orderings. However, for now we are only using ShortLex.'''

from __future__ import print_function
from string import ascii_lowercase
try:
    from string import maketrans
except ImportError:
    maketrans = str.maketrans

class ShortLex():
    ''' This class acts as an ordering system for the ordering 'short lexicographical'
    with respect to the ordered alphabet provided at initialisation. '''
    def __init__(self, alphabet):
        if len(alphabet) > len(ascii_lowercase):
            raise IndexError('Alphabet requested is too large.')
        
        self.alphabet = alphabet
        self.translated_alphabet = ascii_lowercase[:len(alphabet)]
        self.translate_rule = maketrans(self.alphabet, self.translated_alphabet)
        self.lookup = dict(zip(alphabet, range(len(alphabet))))
    
    def __call__(self, A, B):
        return self.ordered(A, B)
    
    def key(self, A):
        return '~' * len(A) + A.translate(self.translate_rule)
    
    def ordered(self, A, B, A_Translated=False, B_Translated=False):
        ''' Return True iff A is strictly before B. '''
        if len(A) < len(B):
            return True
        elif len(A) > len(B):
            return False
        else:
            if not A_Translated: A = A.translate(self.translate_rule)
            if not B_Translated: B = B.translate(self.translate_rule)
            return A < B
    
    def ordered_cyclic(self, A, B, len_A=None, A_Translated=False, B_Translated=False):
        ''' Return True iff A is before or equal to ALL cyclic permutations of B. '''
        
        if len_A is None: len_A = len(A)
        
        # First deal with the cases when A and B are different lengths.
        if len_A > len(B): return False
        if len_A < len(B): return True
        
        if not A_Translated: A = A.translate(self.translate_rule)
        if not B_Translated: B = B.translate(self.translate_rule)
        
        B2 = B * 2
        for i in range(len_A):
            if A > B2[i:i+len_A]: return False
        
        return True
    
    def first(self, words):
        ''' Returns the alphabetically first word in words. '''
        best = words[0]
        for word in words:
            if self.ordered(word, best): best = word
        
        return best
    
    def cyclic_first_permutation(self, *words):
        ''' Returns the first cyclic permutation of any of words.
        Assumes that all words are the same length.
        
        Usage: self.cyclic_first_permutation('foo', 'bar', 'bob') returns
        'arb' when the alphabet is 'abfo'. '''
        
        len_word = len(words[0])
        range_len_word = range(len_word)
        # if any(len(word) != len_word for word in words):
            # print('Error: Words must all be the same length.')
        
        best = words[0]
        start = words[0].translate(self.translate_rule)
        for word in words:
            word_translated2 = word.translate(self.translate_rule) * 2
            
            j = -1
            for i in range_len_word:
                if word_translated2[i:i+len_word] < start:
                    start = word_translated2[i:i+len_word]
                    j = i
            if j > -1: best = (word*2)[j:j+len_word]
        
        return best

