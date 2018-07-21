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
