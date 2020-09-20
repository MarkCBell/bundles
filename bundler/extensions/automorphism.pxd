# distutils: language = c++

from libcpp.vector cimport vector

ctypedef vector[int] IWord

cdef class Automorph:
    cdef int len_alphabet
    cdef int len_alphabet1
    cdef int stop
    cdef int* inverse
    cdef int num_automorphisms
    cdef bint* any_missing
    cdef bint* missing
    cdef int* automorphisms
    
    cdef bint c_before_automorphs(self, IWord& word, IWord& next_word, bint prefix=*)
