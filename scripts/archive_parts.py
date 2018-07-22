import os
import shutil

rel_srce = '../Census/Parts/Word/'
rel_dest = '../Census/Archive/Fibred Knots/S_4_1 Fibred Knots/14 census/Parts/Word'
c = 0
for name in os.listdir(rel_srce):
	p = os.path.join(rel_srce, name)
	q = os.path.join(rel_dest, name)
	
	shutil.move(p, q)
	c += 1

print('%d files archived into: \n%s' % (c, os.path.abspath(rel_dest)))