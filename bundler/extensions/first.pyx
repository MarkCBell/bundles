# distutils: language = c++

from libc.stdlib cimport calloc, free
from libcpp.pair cimport pair
from libcpp.queue cimport queue
from libcpp.set cimport set
from libcpp.vector cimport vector

from bundler.extensions.FSM cimport FSM
from bundler.extensions.automorphism cimport Automorph

ctypedef vector[int] IWord

cdef class FirstInClass:
    cdef int longest_relator
    cdef FSM find_balanced_relators_FSM
    cdef FSM bad_prefix_FSM
    cdef FSM simpler_FSM
    cdef Automorph c_auto
    
    def __init__(self, int longest_relator, FSM find_balanced_relators_FSM, FSM bad_prefix_FSM, FSM simpler_FSM, Automorph c_auto):
        self.longest_relator = longest_relator
        self.find_balanced_relators_FSM = find_balanced_relators_FSM
        self.bad_prefix_FSM = bad_prefix_FSM
        self.simpler_FSM = simpler_FSM
        self.c_auto = c_auto

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
        
        # If it contains any bad prefix or simplification then it can be (trivially) made better.
        if self.bad_prefix_FSM.c_hit(wrd):
            return False
        
        # There is no point in testing whether simpler_FSM hits word already since word ended in next_good_suffix.
        # Check to see if our original word beats itself.
        if not self.c_auto.c_before_automorphs(wrd, wrd, prefix):
            return False
        
        seen.insert(wrd)
        to_do.push(wrd)
        
        next_wrd.resize(len_word)
        
        while not to_do.empty():  # Keep going while there are still unprocessed words in the queue.
            reached = to_do.front()
            to_do.pop()  # Get the next equivalent word to check.
            returns = self.find_balanced_relators_FSM.c_hits(reached, repeat=1 if prefix else 2)
            for i in range(int(returns.size())):
                b = returns[i].first
                replace = returns[i].second
                if b >= len_word + self.longest_relator: break
                len_replace = replace.size()
                if len_replace > len_word: continue
                a = b - len_replace  # There is a replacement to be made between a & b.
                if a >= len_word: continue
                
                # next_wrd = reached[:a] + replace + reached[b:] if b <= len_word else replace[len_word-a:] + reached[b-len_word:a] + replace[:len_word-a]
                k = 0 if a == 0 else len_word - a
                for j in range(len_word):
                    next_wrd[j] = replace[k] if k < len_replace else reached[j]
                    k += 1
                    if k == len_word: k = 0
                
                if seen.count(next_wrd) != 0: continue  # Only consider new words.
                
                # Test for trivial simplifications.
                if self.simpler_FSM.c_hit(next_wrd):
                    return False
                
                if not self.c_auto.c_before_automorphs(wrd, next_wrd, prefix):
                    return False
                
                s = int(seen.size())
                if s == max_tree_size:  # If we've hit the max_tree_size then give up.
                    return True
                
                # Add it to the reachable word list.
                seen.insert(next_wrd)
                to_do.push(next_wrd)
        
        return True


