# distutils: language = c++

from libc.stdlib cimport calloc, free
from libcpp.pair cimport pair
from libcpp.queue cimport queue
from libcpp.set cimport set
from libcpp.vector cimport vector

ctypedef vector[int] IWord

def first_in_class(object self, tuple word, int max_tree_size, bint prefix, int longest_relator):

    cdef int len_word = len(word)  # Let's save some highly used data.
    cdef queue[IWord] to_do  # This is a deque of all words that have yet to be processed.
    cdef set[IWord] seen  # This records all words that we have seen.
    cdef IWord next_word, replace, match, reached
    cdef vector[pair[int, IWord]] returns
    cdef int a, b
    cdef int i, j, k, s
    cdef int len_replace
    
    # If it contains any bad prefix or simplification then it can be (trivially) made better.
    if self.bad_prefix_FSM.hit(word):
        return False
    
    # There is no point in testing whether simpler_FSM hits word already since word ended in next_good_suffix.
    # Check to see if our original word beats itself.
    if not self.c_auto.before_automorphs(word, word, prefix):
        return False
    
    seen.insert(word)
    to_do.push(word)
    
    while not to_do.empty():  # Keep going while there are still unprocessed words in the queue.
        reached = to_do.front()
        to_do.pop()  # Get the next equivalent word to check.
        returns = self.find_balanced_relators_FSM.hits(tuple(reached), repeat=1 if prefix else 2)
        for i in range(int(returns.size())):
            b = returns[i].first
            replace = returns[i].second
            if b >= len_word + longest_relator: break
            len_replace = replace.size()
            if len_replace > len_word: continue
            a = b - len_replace  # There is a replacement to be made between a & b.
            if a >= len_word: continue
            
            next_word.clear()
            for j in range(len_word):
                k = (j - a) % len_word
                next_word.push_back(replace[k] if k < len_replace else reached[j])
            # next_word = reached[:a] + replace + reached[b:] if b <= len_word else replace[len_word-a:] + reached[b-len_word:a] + replace[:len_word-a]
            
            if seen.count(next_word) != 0: continue  # Only consider new words.
            # Test for trivial simplifications.
            
            if self.simpler_FSM.hit(tuple(next_word)):
                return False
            
            if not self.c_auto.before_automorphs(word, tuple(next_word), prefix):
                return False
            
            s = int(seen.size())
            if s == max_tree_size:  # If we've hit the max_tree_size then give up.
                return True
            
            # Add it to the reachable word list.
            seen.insert(next_word)
            to_do.push(next_word)
    
    return True


