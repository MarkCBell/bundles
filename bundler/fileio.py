
import os
import shutil

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

def clean_files(paths):
    ''' Removes requested files (if they exist). '''
    
    for path in paths:
        if os.path.exists(path): os.remove(path)

def concatinate_files(inputs, output):
    ''' Concatenates the contents of all files listed in inputs into the file 'output'. '''
    
    with open(output, 'wb') as destination:
        for path in inputs:
            with open(path, 'rb') as source:
                shutil.copyfileobj(source, destination)


def line_count(path):
    ''' Returns the number of non-empty lines in a file. '''
    
    c = 0
    for line in open(path, 'r'):
        if line != '\n':
            c += 1
    
    return c
