from K_1_1census import build_manifold, load_words_from_file, census_dir, census_file
import multiprocessing
from fractions import gcd
NUM_PROCESSES = min(multiprocessing.cpu_count(),32)

def lens_fillings(inpt):
	index, word = inpt
	lens_words = []
	
	try:
		M = build_manifold(word)
		M.set_peripheral_curves('shortest')
		C = M.cusp_neighborhood()
		C.set_displacement(C.reach())
		A, B = C.translations()
	except:
		print '#',
		return lens_words
	
	if A.imag == 0 or B.real == 0: A, B = B, A
	
	p = int(6 / B.real) + 1
	q = int(6 / A.imag) + 1
	r = int((p*B.imag) / A.imag) + 1
	
	c = 0
	for i in range(-p, p):
		for j in range(-r, q+r):
			if gcd(i, j) != 1: continue
			
			C = i*A + j*B
			if C.real**2 + C.imag**2 > 37: continue
			c += 1
			
			try:
				N = M.copy()
				N.dehn_fill((i, j))
				if len(N.fundamental_group().generators()) == 0: lens_words.append([word, i, j])
			except:
				pass
	
	print '\r', index, c,
	
	return lens_words

if __name__ == '__main__':
	W = load_words_from_file(census_file)
	
	# pool = multiprocessing.Pool(processes = NUM_PROCESSES)
	# results = pool.map(lens_fillings, enumerate(W), 1000)
	results = map(lens_fillings, enumerate(W))
	
	lens_spaces = []
	for result in results:
		lens_spaces.extend(result)
	
	import os
	f = open(os.path.join(census_dir, 'lens_spaces.txt'), 'w')
	f.write('\n'.join('\t'.join(str(cell) for cell in row) for row in lens_spaces))
	f.write('\n')
	
	f.close()
