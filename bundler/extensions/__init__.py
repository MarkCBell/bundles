
from .c_FSM_core import c_FSM
from .c_automorph_core import c_automorph

def build_c_FSM(alphabet, machine, yield_states=None):
    if type(machine[0]) is dict:
        len_alphabet = len(alphabet)
        num_states = len(machine)
        state_names = [x[''] for x in machine]  # The state names are stored in the '' field.
        state_names_index = dict((name, place) for place, name in enumerate(state_names))
        
        formatted_machine = [[-1] * len_alphabet for i in range(num_states)]  # Populate the machine with -1's to begin with.
        for i in range(num_states):
            for j in range(len_alphabet):
                out_state = machine[i][alphabet[j]]
                if out_state in state_names_index: formatted_machine[i][j] = state_names_index[out_state]
        
        machine = formatted_machine
        yield_states = [] if yield_states is None else dict((state_names_index[state], yield_states[state]) for state in yield_states)
    else:
        yield_states = [] if yield_states is None else dict((state, yield_states[state]) for state in yield_states)
    
    return c_FSM(alphabet, [element for row in machine for element in row], [[] if i not in yield_states else list(yield_states[i]) for i in range(len(machine))])
