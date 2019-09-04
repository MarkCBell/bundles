
from collections import defaultdict
from queue import Queue

cdef class FSM:
    cdef str alphabet
    cdef int alphabet_len
    cdef list machine
    cdef int machine_len
    cdef dict yield_states
    cdef dict lookup
    cdef dict distance_to_yield
    
    def __init__(self, alphabet, machine, yield_states):
        self.alphabet = alphabet
        self.alphabet_len = len(self.alphabet)
        self.lookup = dict((letter, index) for index, letter in enumerate(self.alphabet))
        self.machine = machine
        self.machine_len = len(self.machine) // self.alphabet_len
        self.yield_states = yield_states
        
        num_states = len(self.machine) // len(self.alphabet)
        reverse_arrows = defaultdict(list)
        for state in range(num_states):
            for i in range(self.alphabet_len):
                new_state = self.machine[state * self.alphabet_len + i]
                reverse_arrows[new_state].append(state)
        
        to_check = Queue()
        self.distance_to_yield = dict()
        for state in range(num_states):
            if self.yield_states.get(state, []):
                self.distance_to_yield[state] = 0
                to_check.put(state)
        
        while not to_check.empty():
            current = to_check.get()
            for adjacent in reverse_arrows[current]:
                if adjacent not in self.distance_to_yield:
                    self.distance_to_yield[adjacent] = self.distance_to_yield[current] + 1
                    to_check.put(adjacent)
    
    def __call__(self, str word):
        cdef int i, state = 0
        cdef str letter
        for letter in word:
            i = self.lookup.get(letter, -1)
            if i < 0:
                raise ValueError('{} not in alphabet {}'.format(letter, self.alphabet))
            state = self.machine[state * self.alphabet_len + i]
            if state < 0:
                raise ValueError('Invalid transition to state {}'.format(state))
        
        return state
    
    def distance(self, str word):
        return self.distance_to_yield[self(word)]
    
    def hit(self, str word):
        ''' Return whether word meets any state that returns. '''
        return any(self.hits(word))
    
    def hits(self, str word):
        ''' Process word and yield (index, x) for all states that word hits that have things to yield. '''
        cdef int i, index, state = 0
        cdef str letter
        for index, letter in enumerate(word):
            i = self.lookup.get(letter, -1)
            if i < 0:
                raise ValueError('{} not in alphabet {}'.format(letter, self.alphabet))
            state = self.machine[state * self.alphabet_len + i]
            if state < 0:
                raise ValueError('Invalid transition to state {}'.format(state))
            for x in self.yield_states.get(state, []):
                yield (index+1, x)

    def has_cycle(self, str word, int depth=-1):
        cdef list converted_word = [self.lookup[letter] for letter in word]
        cdef int c, state
        
        if depth < 0: depth = self.machine_len
        
        for c in range(depth):
            state = c
            for i in converted_word:
                state = self.machine[state * self.alphabet_len + i]
                if state < 0: break
            
            if state == c:
                return True
        
        return False

