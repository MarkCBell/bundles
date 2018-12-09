
import os
import shutil

def print_words_to_file(table, file, write_method='w'):
    ''' Prints out a word list to a file. '''
    
    if table != []:
        open(file, write_method).write('\n'.join(table) + '\n')
    else:
        open(file, write_method)
    
    return

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
    
    with open(path, 'r') as source:
        return sum(line != '\n' for line in source)
