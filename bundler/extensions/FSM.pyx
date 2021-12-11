# distutils: language = c++

from cpython cimport array
import array

from libc.stdlib cimport calloc, free
from libcpp.pair cimport pair
from libcpp.queue cimport queue
from libcpp.set cimport set
from libcpp.vector cimport vector

from bundler.extensions.FSM cimport FSM

from collections import defaultdict, OrderedDict
from queue import Queue

cdef class FSM:
    def __init__(self, alphabet, machine, yield_states):
        cdef int start
        cdef IWord x
        
        self.alphabet = alphabet
        self.alphabet_len = len(self.alphabet)
        self.machine = array.array('i', machine)
        self.machine_len = len(self.machine) // self.alphabet_len
        self.yield_states = yield_states
        self.has_yield = array.array('i', [1 if self.yield_states.get(state, []) else 0 for state in range(self.machine_len)])
        
        start = 0
        self.yield_states2_starts.push_back(0)
        for i in range(self.machine_len):
            yields = self.yield_states.get(i, [])
            for x in yields:
                self.yield_states2.push_back(x)
            start += len(yields)
            self.yield_states2_starts.push_back(start)
        
        reverse_arrows = defaultdict(list)
        for state in range(self.machine_len):
            for i in range(self.alphabet_len):
                new_state = self.machine.data.as_ints[state * self.alphabet_len + i]
                reverse_arrows[new_state].append(state)
        
        to_check = Queue()
        self.distance_to_yield = dict()
        for state in range(self.machine_len):
            if self.yield_states.get(state, []):
                self.distance_to_yield[state] = 0
                to_check.put(state)
        
        while not to_check.empty():
            current = to_check.get()
            for adjacent in reverse_arrows[current]:
                if adjacent not in self.distance_to_yield:
                    self.distance_to_yield[adjacent] = self.distance_to_yield[current] + 1
                    to_check.put(adjacent)
    
    @classmethod
    def from_dicts(cls, list alphabet, object machine, dict hits):
        ''' Build a cFSM from an ordered dictionary of dictionaries and a dictionary mapping states to hits. '''
        
        assert isinstance(machine, OrderedDict)
        
        state_names = list(machine)
        state_names_index = dict((name, place) for place, name in enumerate(state_names))
        flattened_machine = [state_names_index.get(machine[state_name][letter], -1) for state_name in state_names for letter in alphabet]
        
        return cls(alphabet, flattened_machine, dict((state_names_index[state], hits[state]) for state in hits))
    
    def __reduce__(self):
        return (self.__class__, (self.alphabet, self.machine, self.yield_states))
    
    def __call__(self, tuple word, int state=0):
        cdef int letter
        for letter in word:
            state = self.machine.data.as_ints[state * self.alphabet_len + letter]
            if state < 0:
                raise ValueError('Invalid transition to state {}'.format(state))
        
        return state
    
    def distance(self, tuple word):
        return self.distance_to_yield[self(word)]
    
    cdef bint c_hit(self, IWord& word, int run=-1):
        cdef int index = 0
        cdef int state = 0
        cdef int length = word.size()
        for _ in range(length if run < 0 else run):
            state = self.machine.data.as_ints[state * self.alphabet_len + word[index]]
            if state < 0:
                raise ValueError('Invalid transition to state {}'.format(state))
            if self.has_yield.data.as_ints[state]:
                return True
            index += 1
            if index == length: index = 0
        
        return False
    
    def hit(self, tuple word):
        ''' Return whether word meets any state that yields. '''
        # return any(self.hits(word))
        return self.c_hit(word)
    
    cdef vector[pair[int, IWord]] c_hits(self, IWord& word, int run=-1):
        ''' Process word and yield (index, x) for all states that word hits that have things to yield. '''
        cdef int index = 0
        cdef int state = 0
        cdef int length = word.size()
        cdef int i = 0, j
        cdef vector[pair[int, IWord]] returns
        for _ in range(length if run < 0 else run):
            state = self.machine.data.as_ints[state * self.alphabet_len + word[index]]
            i += 1
            for j in range(self.yield_states2_starts[state], self.yield_states2_starts[state+1]):
                returns.push_back(pair[int, IWord](i, self.yield_states2[j]))
            index += 1
            if index == length: index = 0
        
        return returns
    
    def hits(self, tuple word, int run=-1):
        ''' Process word and yield (index, x) for all states that word hits that have things to yield. '''
        cdef int index = 0, letter
        cdef int state = 0
        cdef int length = len(word)
        cdef int i = 0
        for _ in range(length if run < 0 else run):
            i += 1
            state = self.machine.data.as_ints[state * self.alphabet_len + word[index]]
            if state < 0:
                raise ValueError('Invalid transition to state {}'.format(state))
            for x in self.yield_states.get(state, []):
                yield (i, x)
            index += 1
            if index == length: index = 0

    def has_cycle(self, tuple word, int depth=-1):
        ''' Return whether there is a state such that self(word, state) == state. '''
        cdef array.array converted_word = array.array('i', word)
        cdef int l = len(word)
        cdef int c, state, letter, i
        
        if depth < 0: depth = self.machine_len
        
        for c in range(depth):
            state = c
            for i in range(l):
                letter = converted_word.data.as_ints[i]
                state = self.machine.data.as_ints[state * self.alphabet_len + letter]
                if state < 0: break
            
            if state == c:
                return True
        
        return False

