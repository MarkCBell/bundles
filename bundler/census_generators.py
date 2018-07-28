##### Required modules:
from __future__ import print_function
import os
from time import time
from itertools import islice
try:
    from itertools import ifilter as iterator_filter
except ImportError:
    iterator_filter = filter

from bundler.word_generators import word_generator
from bundler.table_generators import TableGenerator, Table
import bundler.ordering as ordering
import pandas as pd
import bundler.imultiprocessing as imultiprocessing
# from bundler.fileio import *
from bundler.fileio import line_count, print_words_to_file, print_table_to_file, concatinate_files, merge_sorted_csv
from bundler.fileio import clean_folder, clean_files
from bundler.fileio import chunk, dechunk

def basic_filter(X, Y): return True

def dropfirst(n, iterable):
    ''' Drops the first n elements of the iterable. '''
    return islice(iterable, n, None)

def print_summary(all_words, good_words, distinct_words, \
                    grow_time, load_time, thin_time, check_time):
    print('\nSummary:')
    print('\tStatistics:')
    print('\t\tTotal words:\t%d' % all_words)
    print('\t\tGood words:\t%d' % good_words)
    print('\t\tProblem words:\t%d' % (all_words - good_words))
    print('\t\t------------------------------')
    print('\t\tDistinct words:\t%d' % distinct_words)
    print('\t\t------------------------------')
    print('\tTimings:')
    print('\t\tGrow time:\t%fs' % grow_time)
    print('\t\tLoad time:\t%fs' % load_time)
    print('\t\tThin time:\t%fs' % thin_time)
    print('\t\tCheck time:\t%fs' % check_time)
    print('\t\t------------------------------')
    print('\t\tTotal time:\t%fs' % (grow_time + load_time + thin_time + check_time))
    print('\t\t------------------------------')
    return

class census_generator:
    def __init__(self, MCG_generators, arc_neighbours, automorph, MCG_must_contain, option, word_filter=basic_filter, manifold_filter=basic_filter):
        
        self.word_generator = word_generator(MCG_generators, arc_neighbours, automorph, MCG_must_contain, word_filter, option)
        self.table_generator = TableGenerator(MCG_generators, manifold_filter, option)
        self.ordering = ordering.short_lex(MCG_generators)
        self.option = option
    
    # We first define some generators for getting words, blocks and census blocks.
    def get_prefix_blocks(self, depth, num_lines=None):
        if num_lines is None: num_lines = line_count(self.option.word_parts + 'prefixes')
        
        for index, line in enumerate(open(self.option.word_parts + 'prefixes', 'r')):
            yield (self, '%d - %d' % (index, num_lines), line.strip(), depth)
        
        return
    
    def get_word_blocks(self, num_lines=None):
        if num_lines is None: num_lines = line_count(self.option.word_file)
        num_word_blocks = num_lines // self.option.CHUNKSIZE_LOAD + bool(num_lines % self.option.CHUNKSIZE_LOAD)
        
        block, block_count = [], 0
        for line in open(self.option.word_file, 'r'):
            block.append(line.strip())
            if len(block) == self.option.CHUNKSIZE_LOAD:
                block_count += 1
                yield (self, '%d-%d' % (block_count, num_word_blocks), block)
                
                block = []
        
        block_count += 1
        yield (self, '%d-%d' % (block_count, num_word_blocks), block)
        
        return
    
    def get_census_blocks(self, num_lines=None):
        # We also make sure to record what words to skip when compiling lists.
        if num_lines is None: num_lines=line_count(self.option.good_file)
        
        num_census_blocks = num_lines // self.option.CHUNKSIZE_THIN + 1
        for index, df in enumerate(pd.read_csv(self.option.good_file, chunksize=self.option.CHUNKSIZE_THIN, index_col='word')):
            yield (self, Table(self.ordering, self.option, df), '%d-%d' % (index+1, num_census_blocks))
        
        return
    
    def build_census(self, depth, prebuilt=0, skip=0):
        ''' Builds a census of hyperbolic surface bundles over the circle.
        The census is built to depth 'depth' and we assume that there is a
        prebuilt structure specified by 'prebuilt':
            'prebuilt' == 0 ==> Assumes nothing (default),
            'prebuilt' == 1 ==> Assumes any existing word blocks are correct,
            'prebuilt' == 2 ==> Assumes word list is complete,
            'prebuilt' == 3 ==> Assumes any existing volume blocks are correct,
            'prebuilt' == 4 ==> Assumes volume list is complete,
            'prebuilt' == 5 ==> Assumes any existing census blocks are correct.
        '''
        
        if depth == 0:
            print(self.build_census.__doc__.replace('\t', ' '))
            exit(0)
        
        assert depth > 0 and prebuilt >= 0
        
        # These will store the total running times
        # and the number of words at each stage.
        grow_time, load_time, thin_time, check_time = 0, 0, 0, 0
        all_words, good_words, distinct_words = 0, 0, 0
        
        # Note: Most of this is now avoided by working with generator expressions. However,
        # as we can't use multiprocessing.Pool.map over a generator we use my custom
        # imultiprocessing library instead now.
        
        start = time()
        if self.option.SHOW_PROGRESS: print('Generating words.')
        if prebuilt < 1:
            clean_folder(self.option.word_parts_dir)
            words, prefixes = self.word_generator.valid_suffixes(self.option.MASTER_PREFIX, self.option.PREFIX_DEPTH, depth)
            if self.option.SHOW_PROGRESS: print('\rTraversing prefix tree: DONE' + ' ' * depth)
            print_words_to_file(words, self.option.word_parts + 'start_words')
            print_words_to_file(prefixes, self.option.word_parts + 'prefixes')
        
        if prebuilt < 2:
            load_inputs = iterator_filter(lambda I: not os.path.isfile(self.option.word_parts + I[1]), dropfirst(skip, self.get_prefix_blocks(depth)))
            skip = 0
            
            if self.option.MULTIPROCESS_GROW:
                imultiprocessing.imap(valid_suffixes_map, load_inputs, self.option.NUM_PROCESSES, return_results=False)
            else:
                for I in load_inputs:
                    valid_suffixes_map(I)
            
            if self.option.SHOW_PROGRESS: print('\rTraversing word tree: DONE          ')
            
            if self.option.SHOW_PROGRESS: print('Combining files.')
            labels = [I[1] for I in self.get_prefix_blocks(depth)]
            concatinate_files([self.option.word_parts + 'start_words'] + [self.option.word_parts + label for label in labels], self.option.word_file)
        
        grow_time = time() - start
        all_words = line_count(self.option.word_file)
        if self.option.SHOW_TIMINGS: print('Grow time: %fs' % grow_time)
        if self.option.SHOW_PROGRESS: print('\t%d possible words to check.' % all_words)
        
        start = time()
        if self.option.SHOW_PROGRESS: print('Collecting volume information.')
        if prebuilt < 3:
            clean_folder(self.option.good_parts_dir)
        
        if prebuilt < 4:
            load_inputs = iterator_filter(lambda I: not os.path.isfile(self.option.good_parts + I[1]), self.get_word_blocks(all_words))
            skip = 0
            
            if self.option.MULTIPROCESS_LOAD:
                imultiprocessing.imap(determine_volumes_words_map, load_inputs, self.option.NUM_PROCESSES, return_results=False)
            else:
                for I in load_inputs:
                    determine_volumes_words_map(I)
            
            if self.option.SHOW_PROGRESS: print('\rCollecting volume information: DONE          ')
            
            if self.option.SHOW_PROGRESS: print('Combining files.')
            labels = [I[1] for I in self.get_word_blocks(all_words)]
            merge_sorted_csv([self.option.good_parts + label for label in labels], self.option.good_file, key=lambda row: float(row.split(',')[3]))
        
        load_time = time() - start
        good_words = line_count(self.option.good_file)
        if self.option.SHOW_TIMINGS: print('Load time: %fs' % load_time)
        if self.option.SHOW_PROGRESS: print('\t%d good words loaded.' % good_words)
        
        start = time()
        if self.option.SHOW_PROGRESS: print('Thinning blocks.')
        if prebuilt < 5:
            clean_folder(self.option.census_parts_dir)
        
        if prebuilt < 6:
            load_inputs = iterator_filter(lambda I: not os.path.isfile(self.option.census_parts + I[2]), self.get_census_blocks(good_words))
            skip = 0
            
            if self.option.MULTIPROCESS_THIN:
                imultiprocessing.imap(remove_duplicates_words_map, load_inputs, self.option.NUM_PROCESSES, return_results=False)
            else:
                for I in load_inputs:
                    remove_duplicates_words_map(I)
            
            if self.option.SHOW_PROGRESS: print('Thinning: DONE          ')
            
            if self.option.SHOW_PROGRESS: print('Combining files.')
            labels = [I[2] for I in self.get_census_blocks(good_words)]
            merge_sorted_csv([self.option.census_parts + label for label in labels], self.option.census_file, key=lambda row: float(row.split(',')[3]))
        
        thin_time = time() - start
        distinct_words = line_count(self.option.census_file)
        if self.option.SHOW_TIMINGS: print('Thin time: %fs' % thin_time)
        if self.option.SHOW_PROGRESS: print('\t%d distinct words.' % distinct_words)
        
        if self.option.SHOW_TIMINGS: print_summary(all_words, good_words, distinct_words, grow_time, load_time, thin_time, check_time)
        
        return

# In order to be able to multiprocess these we need to be able to refer
# to various functions globally. Otherwise it would just be
# an instance copy of the function and so lost when the objects are passed
# around by pickling.
def valid_suffixes_map(X):
    self, label, prefix, depth = X
    if self.option.SHOW_PROGRESS: print('\rLoading suffixes of prefix %s' % label)
    
    words, prefixes = self.word_generator.valid_suffixes(prefix, depth)
    
    print_words_to_file(words, self.option.word_parts + label)
    
    return

def determine_volumes_words_map(X):
    self, label, words = X
    if self.option.SHOW_PROGRESS: print('\rCollecting volume information from block: %s' % label)
    
    table = self.table_generator(words)
    table.to_csv(self.option.good_parts + label)
    
    return

def remove_duplicates_words_map(X):
    self, table, label = X
    if self.option.SHOW_PROGRESS: print('\rRemoving duplicates of block: %s' % label)
    table.filter_duplicates()
    table.to_csv(self.option.census_parts + label)
    return
    
    clean_files(self.option.not_problem_parts + label)  # Get rid of any old not_problem_words.
    remaining_words = list(words)
    len_word_block = self.option.CHUNKSIZE_THIN  # We really should halve this because we're going to need to stick pairs of these together.
    block_count = 0  # How many blocks have we written out.
    while len(remaining_words) > 0:
        if self.option.SHOW_PROGRESS: print('\rRemoving duplicates of block: %s, %d remaining' % (label, len(remaining_words)))    
        
        remaining_word_blocks = chunk(remaining_words, len_word_block)
        if self.option.SHOW_PROGRESS: print('Loading subblock %d in block: %s.' % (block_count, label))
        master_table, problem_words, filtered_words = self.table_generator.convert_words_table(remaining_word_blocks[0])
        print_words_to_file(problem_words, self.option.not_problem_parts + label, 'a')  # Remember to save out these problem_words.
        self.table_generator.remove_duplicates_table(master_table)
        master_table = [row for row in master_table if row is not None]
        
        for i in range(1, len(remaining_word_blocks)):
            if self.option.SHOW_PROGRESS: print('Filtering subblock %d in block %s against subblock %d - %d' % (block_count, label, i, len(remaining_word_blocks)))
            table, problem_words, filtered_words = self.table_generator.convert_words_table(remaining_word_blocks[i])
            print_words_to_file(problem_words, self.option.not_problem_parts + label, 'a')  # Remember to save out these problem_words.
            temp_table = master_table + table
            self.table_generator.remove_duplicates_table(temp_table)
            filtered_words = set(row[0] for row in temp_table if row is not None)
            master_table = [row for row in master_table if row[0] in filtered_words]
            remaining_word_blocks[i] = [word for word in remaining_word_blocks[i] if word in filtered_words]
        
        if self.option.SHOW_PROGRESS: print('Removing reskip_words.')
        for j in range(len(master_table)):
            if master_table[j][0] in reskip_words:
                master_table[j] = None
        
        if self.option.SHOW_PROGRESS: print('Saving subblock %d.' % block_count)
        print_table_to_file(master_table, self.option.census_parts + label + ' - ' + str(block_count))
        block_count += 1
        
        remaining_words = dechunk(remaining_word_blocks[1:])
    
    if self.option.SHOW_PROGRESS: print('Combining files in block: %s.' % label)
    concatinate_files([self.option.census_parts + label + ' - ' + str(i) for i in range(block_count)], self.option.census_parts + label, delete_input_files_after=True)
    
    return

