
from queue import Queue
from collections import OrderedDict

from .FSM import FSM
from .first import FirstInClass

EMPTY_TUPLE = tuple()

def word_accepting_FSM(alphabet, acceptable_words, transform=lambda x: x):
    ''' Given an alphabet and a list of acceptable_words in that alphabet, this
        builds a FSM that hits all occurances of these words within a given string.
        
        Uses the Aho-Corasick string matching algorithm. '''
    
    if '' in acceptable_words:
        raise ValueError('Empty word cannot be acceptable.')
    
    machine = OrderedDict()
    tree = Queue()
    tree.put(EMPTY_TUPLE)
    all_states = set([EMPTY_TUPLE])
    acceptable_words_set = set(acceptable_words)
    acceptable_words_prefixes_set = set(w[:i+1] for w in acceptable_words for i in range(len(w)))
    accepting_states = dict()
    
    suffixes = lambda word: set(word[j:] for j in range(len(word)))
    
    # Now grow the machine.
    while not tree.empty():
        word = tree.get()
        accepting_states[word] = set(transform(item) for item in suffixes(word).intersection(acceptable_words_set))
        
        state = dict()
        
        for letter in alphabet:
            state[letter] = EMPTY_TUPLE
            next_word = word + (letter,)
            
            for i in range(len(next_word)-1, -1, -1):
                if next_word[-i-1:] in acceptable_words_prefixes_set:
                    state[letter] = next_word[-i-1:]
                    
                    if state[letter] not in all_states:
                        tree.put(state[letter])
                        all_states.add(state[letter])
                    
                    break
        
        machine[word] = state
    
    return FSM.from_dicts(alphabet, machine, accepting_states)

def action_FSM(actions, seeds, max_depth):
    ''' Generates a FSM detailing how action moves about all states within max_depth of a seed. '''
    
    machine = OrderedDict()
    to_check = Queue()
    depths = dict()
    for seed in seeds:
        if seed not in depths:
            to_check.put(seed)
            depths[seed] = 0
    
    while not to_check.empty():
        current = to_check.get()
        current_depth = depths[current]
        
        # Determine the result of each action on current.
        arrows = dict()
        for letter, action in actions.items():  # We explore in every direction.
            arrows[letter] = action(current)
            if current_depth < max_depth and arrows[letter] not in depths:
                depths[arrows[letter]] = current_depth + 1
                to_check.put(arrows[letter])
        
        machine[current] = arrows
    
    return FSM.from_dicts(sorted(actions), machine, dict())

def CNF_FSM(alphabet, clauses):
    ''' Generate an FSM that determines whether a CNF is satisfied. '''
    
    clauses = list(clauses)
    states = [i for i in range(2**len(clauses))]
    
    flags = dict((letter, sum(2**i for i, clause in enumerate(clauses) if letter in clause)) for letter in alphabet)
    
    machine = OrderedDict()
    accepting_states = {states[-1]: [tuple()]}  # Just need to return something to make this a yield state.
    for state in states:
        arrows = dict()
        for letter in alphabet:
            arrows[letter] = state | flags[letter]
        
        machine[state] = arrows
    
    return FSM.from_dicts(alphabet, machine, accepting_states)

