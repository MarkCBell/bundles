from libc.stdlib cimport calloc, free

from bundler.extensions.automorphism cimport Automorph

cdef bint is_cyclic_ordered(int* A, int* B, int l, int* S, int* f):
    ''' Return whether A is <= all cyclic perumtations of B.
    
    Equivalent to:
        return all(A <= B[i:] + B[:i] for i in range(len(A))) '''
    # Use Booths algorithm to find j, the best starting point. See:
    # https://en.wikipedia.org/wiki/Lexicographically_minimal_string_rotation#Booth's_Algorithm
    cdef int i, j = 0, last, ll = 2 * l
    
    for i in range(l):  # S = B + B
        S[i] = S[i+l] = B[i]
    for i in range(ll):  # f = [-1] * len(S)
        f[i] = -1
    
    for i in range(1, ll):
        si = S[i]
        last = f[i - j - 1]
        while last != -1 and si != S[j + last + 1]:
            if si < S[j + last + 1]:
                j = i - last - 1
            last = f[last]
        if si != S[j + last + 1]:
            if si < S[j]:  # j+last+1 = j
                j = i
            f[i - j] = -1
        else:
            f[i - j] = last + 1
    
    # Compare A to the (inplace) cycled B.
    for i in range(l):
        if A[i] < B[j]:
            return True  # A < cycled(B)
        elif A[i] > B[j]:
            return False  # A > cycled(B)
        j += 1
        if j == l:  # Wrap around.
            j = 0
    
    return True  # A == cycled(B)

cdef class Automorph:
    
    def __init__(self, list alphabet, list inverse, list automorphisms):
        cdef list missing, auto
        cdef int i, j
        self.len_alphabet = len(alphabet)
        self.len_alphabet1 = self.len_alphabet + 1
        self.stop = self.len_alphabet
        self.inverse = <int *> calloc(self.len_alphabet1, sizeof(int))  # +1 for stop character.
        for i in range(self.len_alphabet):
            self.inverse[i] = inverse[i]
        self.inverse[self.len_alphabet] = self.stop
        
        self.num_automorphisms = len(automorphisms)
        self.any_missing = <bint *> calloc(self.num_automorphisms, sizeof(bint))
        self.missing = <bint *> calloc(self.num_automorphisms * self.len_alphabet1, sizeof(bint))
        self.automorphisms = <int *> calloc(self.num_automorphisms * self.len_alphabet1, sizeof(int*))
        for i in range(self.num_automorphisms):
            if automorphisms[i][0]: self.any_missing[i] = 1
            for j in automorphisms[i][0]:
                self.missing[self.len_alphabet1 * i + j] = 1
            for j in range(self.len_alphabet):
                self.automorphisms[i * self.len_alphabet1 + j] = automorphisms[i][1][j]
            self.automorphisms[i * self.len_alphabet1 + self.len_alphabet] = self.stop
    
    def __del__(self):
        free(self.inverse)
        free(self.any_missing)
        free(self.missing)
        free(self.automorphisms)
    
    cdef bint c_before_automorphs(self, IWord& word, IWord& next_word, bint prefix=False):
        ''' Return whether word is before all cyclic permutations of all automorphs of next_word and next_word^-1. '''
        cdef int l0 = word.size()
        cdef int i, j, l = l0 + (1 if prefix else 0)
        cdef bint bad
        cdef int* wd = <int *> calloc(l, sizeof(int))
        cdef int* nxt_wd = <int *> calloc(l, sizeof(int))
        cdef int* nxt_wd_inv = <int *> calloc(l, sizeof(int))
        cdef int* automorphed = <int *> calloc(l, sizeof(int))
        
        # Scratch memory for Booth's algorithm.
        cdef int *tmp1 = <int *> calloc(2*l, sizeof(int))
        cdef int *tmp2 = <int *> calloc(2*l, sizeof(int))
        
        try:
            # Map word into a C array. Add a stop character to the end if required.
            for i in range(l0):
                wd[i] = word[i]
            if prefix:
                wd[l0] = self.stop
            
            # Map next_word into a C array. Add a stop character to the end if required.
            for i in range(l0):
                nxt_wd[i] = next_word[i]
            if prefix:
                nxt_wd[l0] = self.stop
            
            # Map next_word^-1 into a C array. Since nxt_wd already contains this, we reverse and inverse it.
            for i in range(l):
                nxt_wd_inv[i] = self.inverse[nxt_wd[l-i-1]]
            
            for i in range(self.num_automorphisms):
                if prefix and self.any_missing[i]: continue
                # if any(letter in next_word for letter in self.missing[i]): continue
                bad = False
                for j in range(l):
                    if self.missing[self.len_alphabet1 * i + nxt_wd[j]] == 1:
                        bad = True
                        break
                if bad: continue
                
                # Construct and test automorph(next_word).
                for j in range(l):
                    automorphed[j] = self.automorphisms[i * self.len_alphabet1 + nxt_wd[j]]
                if not is_cyclic_ordered(wd, automorphed, l, tmp1, tmp2): return False
                
                # Construct and test automorph(next_word^-1).
                for j in range(l):
                    automorphed[j] = self.automorphisms[i * self.len_alphabet1 + nxt_wd_inv[j]]
                if not is_cyclic_ordered(wd, automorphed, l, tmp1, tmp2): return False
            
            return True
        finally:
            free(wd)
            free(nxt_wd)
            free(nxt_wd_inv)
            free(automorphed)
            free(tmp1)
            free(tmp2)

    def before_automorphs(self, tuple word, tuple next_word, bint prefix=False):
        return self.c_before_automorphs(word, next_word, prefix)
        
        # for missing, automorphism in self.automorphisms:
            # if not (missing and prefix) and all(letter not in next_word for letter in missing) and not is_cyclic_ordered(word, tuple(automorphism[letter] for letter in other), prefix):
                # return False
        # 
        # return True
