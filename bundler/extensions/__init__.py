
try:
    from Queue import Queue
except ImportError:
    from queue import Queue
from collections import OrderedDict

from .FSM import FSM
from .automorphism import Automorph
from .ordering import ShortLex

def suffixes(word):
    return set(word[j:] for j in range(len(word)))

def build_c_FSM(alphabet, machine, hits):
    ''' Build a cFSM from an ordered dictionary of dictionaries and a dictionary mapping states to hits. '''
    
    assert isinstance(alphabet, str)
    assert isinstance(machine, OrderedDict)
    assert isinstance(hits, dict)
    
    state_names = list(machine)
    state_names_index = dict((name, place) for place, name in enumerate(state_names))
    flattened_machine = [state_names_index.get(machine[state_name][letter], -1) for state_name in state_names for letter in alphabet]
    
    return FSM(alphabet, flattened_machine, dict((state_names_index[state], hits[state]) for state in hits))

def word_accepting_FSM(alphabet, acceptable_words):
    ''' Given an alphabet and a list of acceptable_words in that alphabet, this
        builds a FSM that hits all occurances of these words within a given string.
        
        Uses the Aho-Corasick string matching algorithm. '''
    
    if '' in acceptable_words:
        raise ValueError('Empty word cannot be acceptable.')
    
    machine = OrderedDict()
    tree = Queue()
    tree.put('')
    all_states = set([''])
    acceptable_words_set = set(acceptable_words)
    acceptable_words_prefixes_set = set(w[:i+1] for w in acceptable_words for i in range(len(w)))
    accepting_states = dict()
    
    # Now grow the machine.
    while not tree.empty():
        word = tree.get()
        accepting_states[word] = suffixes(word).intersection(acceptable_words_set)
        
        state = dict()
        
        for letter in alphabet:
            state[letter] = ''
            next_word = word + letter
            
            for i in range(len(next_word)-1, -1, -1):
                if next_word[-i-1:] in acceptable_words_prefixes_set:
                    state[letter] = next_word[-i-1:]
                    
                    if state[letter] not in all_states:
                        tree.put(state[letter])
                        all_states.add(state[letter])
                    
                    break
        
        machine[word] = state
    
    return build_c_FSM(alphabet, machine, accepting_states)

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
    
    return build_c_FSM(''.join(sorted(actions)), machine, dict())

def CNF_FSM(alphabet, clauses):
    ''' Generate an FSM that determines whether a CNF is satisfied. '''
    
    clauses = list(clauses)
    states = [i for i in range(2**len(clauses))]
    
    flags = dict((letter, sum(2**i for i, clause in enumerate(clauses) if letter in clause)) for letter in alphabet)
    
    machine = OrderedDict()
    accepting_states = {states[-1]: [True]}
    for state in states:
        arrows = dict()
        for letter in alphabet:
            arrows[letter] = state | flags[letter]
        
        machine[state] = arrows
    
    return build_c_FSM(alphabet, machine, accepting_states)

