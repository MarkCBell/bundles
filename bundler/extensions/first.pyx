# distutils: language = c++

from libc.stdlib cimport calloc, free
from libcpp.pair cimport pair
from libcpp.queue cimport queue
from libcpp.set cimport set
from libcpp.vector cimport vector

from bundler.extensions.FSM cimport FSM

ctypedef vector[int] IWord

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

cdef class FirstInClass:
    cdef int longest_relator
    cdef FSM find_balanced_relators_FSM
    cdef FSM bad_prefix_FSM
    cdef FSM simpler_FSM
    
    cdef int len_alphabet
    cdef int len_alphabet1
    cdef int stop
    cdef int* inverse
    cdef int num_automorphisms
    cdef bint* any_missing
    cdef bint* missing
    cdef int* automorphisms
    
    def __init__(self, list alphabet, list inverse, int longest_relator, FSM find_balanced_relators_FSM, FSM bad_prefix_FSM, FSM simpler_FSM, list automorphisms):
        cdef list missing, auto
        cdef int i, j
        self.longest_relator = longest_relator
        self.find_balanced_relators_FSM = find_balanced_relators_FSM
        self.bad_prefix_FSM = bad_prefix_FSM
        self.simpler_FSM = simpler_FSM
        
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
    
    cdef bint c_before_automorphs(self, IWord& word, IWord& next_word, bint prefix, int* tmp):
        ''' Return whether word is before all cyclic permutations of all automorphs of next_word and next_word^-1.
        
        Requires memory for 8*l temporary integers. '''
        cdef int l0 = word.size()
        cdef int i, j, l = l0 + (1 if prefix else 0)
        cdef bint bad
        
        cdef int* wd = tmp + 0*l
        cdef int* nxt_wd = tmp + 1*l
        cdef int* nxt_wd_inv = tmp + 2*l
        cdef int* automorphed = tmp + 3*l
        
        # Scratch memory for Booth's algorithm.
        cdef int *tmp1 = tmp + 4*l
        cdef int *tmp2 = tmp + 6*l
        
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
                if self.missing[self.len_alphabet1 * i + nxt_wd[j]]:
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

    def is_first(self, tuple word, bint prefix, int max_tree_size):
        ''' Determines if a word is lex first in its class.
        
        Uses relators and automorphs to find alternative representatives. Gives up after finding
        max_tree_size alternatives, if max_tree_size <= 0 this will run until it has found all
        equivalent words of the same length in which case the result returned is absolutely correct.
        
        If prefix == True, only prefix stable stable moves are performed, i.e. if it is discovered
        that u ~ v then uw ~ vw for all words w.
        
        This function is the heart of the grow phase, speed is critical here.'''

        cdef IWord wrd = word
        cdef int len_word = wrd.size()  # Let's save some highly used data.
        cdef queue[IWord] to_do  # This is a deque of all words that have yet to be processed.
        cdef set[IWord] seen  # This records all words that we have seen.
        cdef IWord next_wrd, replace, match, reached
        cdef vector[pair[int, IWord]] returns
        cdef int a, b
        cdef int i, j, k, s
        cdef int len_replace
        
        cdef int l = len_word + (1 if prefix else 0)
        cdef int nl = len_word + (1 if not prefix else 0)
        cdef int len_word_relators = len_word if prefix else len_word + self.longest_relator
        
        # Scratch memory for automorphism testing.
        cdef int* tmp = <int *> calloc(8*l, sizeof(int))
        
        try:
            # If it contains any bad prefix or simplification then it can be (trivially) made better.
            if self.bad_prefix_FSM.c_hit(wrd):
                return False
            
            # There is no point in testing whether simpler_FSM hits word already since word ended in next_good_suffix.
            # Check to see if our original word beats itself.
            if not self.c_before_automorphs(wrd, wrd, prefix, tmp):
                return False
            
            seen.insert(wrd)
            to_do.push(wrd)
            
            next_wrd.resize(len_word)
            
            while not to_do.empty():  # Keep going while there are still unprocessed words in the queue.
                reached = to_do.front()
                to_do.pop()  # Get the next equivalent word to check.
                returns = self.find_balanced_relators_FSM.c_hits(reached, run=len_word_relators)
                for i in range(int(returns.size())):
                    b = returns[i].first
                    replace = returns[i].second
                    len_replace = replace.size()
                    if len_replace > len_word: continue
                    a = b - len_replace  # There is a replacement to be made between a & b.
                    if a >= len_word: continue
                    
                    # next_wrd = reached[:a] + replace + reached[b:] if b <= len_word else replace[len_word-a:] + reached[b-len_word:a] + replace[:len_word-a]
                    k = 0 if a == 0 else len_word - a  # k = -a % len_word.
                    for j in range(len_word):  # k = (j - a) % len_word
                        next_wrd[j] = replace[k] if k < len_replace else reached[j]
                        k += 1
                        if k == len_word: k = 0
                    
                    if seen.count(next_wrd) != 0: continue  # Only consider new words.
                    
                    # Test for trivial simplifications.
                    if self.simpler_FSM.c_hit(next_wrd, run=nl):
                        return False
                    
                    if not self.c_before_automorphs(wrd, next_wrd, prefix, tmp):
                        return False
                    
                    s = seen.size()
                    if s == max_tree_size:  # If we've hit the max_tree_size then give up.
                        return True
                    
                    # Add it to the reachable word list.
                    seen.insert(next_wrd)
                    to_do.push(next_wrd)
            
            return True
        finally:
            free(tmp)

