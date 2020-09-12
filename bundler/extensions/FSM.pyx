from cpython cimport array
import array

from collections import defaultdict
from queue import Queue

cdef class FSM:
    cdef list alphabet
    cdef int alphabet_len
    cdef array.array machine
    cdef int machine_len
    cdef dict yield_states
    cdef dict distance_to_yield
    cdef array.array has_yield
    
    def __init__(self, alphabet, machine, yield_states):
        self.alphabet = alphabet
        self.alphabet_len = len(self.alphabet)
        self.machine = array.array('i', machine)
        self.machine_len = len(self.machine) // self.alphabet_len
        self.yield_states = yield_states
        self.has_yield = array.array('i', [1 if self.yield_states.get(state, []) else 0 for state in range(self.machine_len)])
        
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
    
    def __call__(self, tuple word, int state=0):
        cdef int letter
        for letter in word:
            state = self.machine.data.as_ints[state * self.alphabet_len + letter]
            if state < 0:
                raise ValueError('Invalid transition to state {}'.format(state))
        
        return state
    
    def distance(self, tuple word):
        return self.distance_to_yield[self(word)]
    
    def hit(self, tuple word):
        ''' Return whether word meets any state that yields. '''
        # return any(self.hits(word))
        cdef int index, letter
        cdef int state = 0
        for index, letter in enumerate(word):
            state = self.machine.data.as_ints[state * self.alphabet_len + letter]
            if state < 0:
                raise ValueError('Invalid transition to state {}'.format(state))
            if self.has_yield.data.as_ints[state]:
                return True
        
        return False
    
    def hits(self, tuple word):
        ''' Process word and yield (index, x) for all states that word hits that have things to yield. '''
        cdef int index, letter
        cdef int state = 0
        for index, letter in enumerate(word):
            state = self.machine.data.as_ints[state * self.alphabet_len + letter]
            if state < 0:
                raise ValueError('Invalid transition to state {}'.format(state))
            for x in self.yield_states.get(state, []):
                yield (index+1, x)

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

