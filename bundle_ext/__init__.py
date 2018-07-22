from .c_FSM_core import c_FSM
from .c_automorph_core import c_automorph
from .c_matrix_core import c_matrix

def build_c_matrix(M):
	if any(len(row) != len(M) for row in M):
		raise ValueError('Cannot create non-square matrices.')
	
	return c_matrix(len(M), [element for row in M for element in row])

def convert_action_to_matrix(generators_and_inverses, action):
	generators = [n for n in generators_and_inverses if n.islower()]
	num_generators = len(generators)
	
	M = [[0] * num_generators for i in range(num_generators)]
	for i in range(num_generators):
		g = generators[i]
		if g in action:
			for j in range(num_generators):
				M[j][i] = action[g].count(generators[j]) - action[g].count(generators[j].swapcase())
	
	return build_c_matrix(M)

def matrix_as_string(M):
	d = M.dimension()
	L = M.matrix()
	
	return '\n'.join(str(L[i:i+d]) for i in range(0, d**2, d))

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
