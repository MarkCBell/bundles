##### Required modules:
import os
import shutil
from tempfile import mkstemp
from itertools import chain
try:
	from Queue import PriorityQueue
except ImportError:
	from queue import PriorityQueue

def print_table_to_file(table, file, write_method='w'):
	''' Prints out a table (excluding manifold objects) to a file. '''
	
	if table != [] and not all(row is None for row in table):
		open(file, write_method).write('\n'.join('\t'.join(str(r) for i, r in enumerate(row) if i != 1) for row in table if row is not None) + '\n')
	else:
		open(file, write_method)
	
	return

def print_words_to_file(table, file, write_method='w'):
	''' Prints out a word list to a file. '''
	
	if table != []:
		open(file, write_method).write('\n'.join(table) + '\n')
	else:
		open(file, write_method)
	
	return

def load_words_from_file(file):
	''' Loads a list of words from a file. '''
	
	if os.path.exists(file):
		return [data[0] for data in (line.strip().split('\t') for line in open(file, 'r')) if data[0] != '' and data[0][0] != '#']
	else:
		return []

def clean_files(*paths):
	''' Removes requested files (if they exist). '''
	
	for path in paths:
		if os.path.exists(path): os.remove(path)
	
	return

def clean_folder(path):
	''' Removes all files in a folder. '''
	
	files = filter(lambda f: os.path.isfile(f), [os.path.join(path, f) for f in os.listdir(path)])
	clean_files(*files)

def concatinate_files(inputs, output, delete_input_files_after=False):
	''' Concatenates the contents of all files listed in inputs into the file 'output'. '''
	
	destination = open(output, 'wb')
	for path in inputs:
		shutil.copyfileobj(open(path, 'rb'), destination)
	destination.close()

	if delete_input_files_after: clean_files(*inputs)
	
	return

def line_count(path):
	''' Returns the number of non-empty lines in a file. '''
	
	c = 0
	for line in open(path, 'r'):
		if line != '\n':
			c += 1
	
	return c

def merge_sorted_files(input_paths, output_path, key=lambda x: x, split=lambda x: x.split('\t'), delete_input_files_after=False):
	''' Merges several files of sorted data into a single file using minimal memory. '''
	
	MAX_OPEN_FILES = 100  # Python can only open so many file handles.
	
	num_files = len(input_paths)
	if num_files <= MAX_OPEN_FILES:
		files = [open(path, 'r') for path in input_paths]
		
		Q = PriorityQueue()
		for i in range(num_files):
			R = files[i].readline()
			if R: Q.put((key(split(R)), R, i))
		
		output_file = open(output_path, 'w')
		while not Q.empty():
			V, R, i = Q.get()
			
			output_file.write(R)
			new_R = files[i].readline()
			if new_R: Q.put((key(split(new_R)), new_R, i))
		
		output_file.close()
		for i in range(num_files):
			files[i].close()
	else:  # So for large numbers of files we divide and conquer.
		temp_outputs = []
		for i in range(0, num_files, MAX_OPEN_FILES):
			f, output = mkstemp()
			os.close(f)
			merge_sorted_files(input_paths[i:i+MAX_OPEN_FILES], output, key)
			temp_outputs.append(output)
		
		merge_sorted_files(temp_outputs, output_path, key, delete_input_files_after=True)
	
	if delete_input_files_after: clean_files(*input_paths)
	
	return

def pad_list(L, required_length, padding=0, function=lambda x: x):
	return [function(x) for x in L + [padding] * max(required_length - len(L), 0)][:required_length]

def chunk(iterable, n):
	return [iterable[i:i+n] for i in range(0, len(iterable), n)]

def dechunk(iterables):
	return list(chain(*iterables))

