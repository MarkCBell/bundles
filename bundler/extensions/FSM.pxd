# distutils: language = c++

from cpython cimport array
import array

from libcpp.pair cimport pair
from libcpp.vector cimport vector

ctypedef vector[int] IWord

cdef class FSM:
    cdef list alphabet
    cdef int alphabet_len
    cdef array.array machine
    cdef int machine_len
    cdef dict yield_states
    cdef dict distance_to_yield
    cdef array.array has_yield
    
    cdef vector[IWord] yield_states2
    cdef vector[int] yield_states2_starts
    
    cdef bint c_hit(self, IWord& word)
    cdef vector[pair[int, IWord]] c_hits(self, IWord& word, int repeat=*)

