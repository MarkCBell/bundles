
from __future__ import print_function
from collections import namedtuple
from glob import glob
from multiprocessing import Pool
from random import randint
from time import time
import numpy as np
import os
import pandas as pd
try:
    from itertools import ifilter
except ImportError:
    ifilter = filter

import bundler

def clean_files(paths):
    ''' Removes requested files (if they exist). '''
    
    for path in paths:
        if os.path.exists(path): os.remove(path)

def basic_filter(self, x): return True

class CensusGenerator():
    def __init__(self, MCG_generators, arc_neighbours, automorph, MCG_must_contain, options, word_filter=basic_filter, manifold_filter=basic_filter):
        self.word_generator = bundler.WordGenerator(MCG_generators, arc_neighbours, automorph, MCG_must_contain, word_filter, options)
        self.ordering = bundler.ShortLex(MCG_generators)
        self.options = options
        self.word_filter = word_filter
        self.manifold_filter = manifold_filter
    
    # We first define some generators for getting words, blocks and census blocks.
    def get_prefix_blocks(self, depth, num_lines=None):
        df = pd.read_csv(self.options.word_parts.format('prefixes'))
        
        for index, row in df.iterrows():
            yield (self, '%d-%d' % (index+1, len(df)), row.word, depth)
    
    def get_word_blocks(self):
        for index, df in enumerate(pd.read_csv(self.options.word_file, chunksize=self.options.CHUNKSIZE_LOAD)):
            yield (self, str(index), df)
    
    def build_census(self, depth, prebuilt=0):
        ''' Builds a census of hyperbolic surface bundles over the circle.
        The census is built to depth 'depth' and we assume that there is a
        prebuilt structure specified by 'prebuilt':
            'prebuilt' == 0 ==> Assumes nothing (default),
            'prebuilt' == 1 ==> Assumes any existing word blocks are correct,
            'prebuilt' == 2 ==> Assumes word list is complete,
            'prebuilt' == 3 ==> Assumes any existing volume blocks are correct,
            'prebuilt' == 4 ==> Assumes volume list is complete,
        '''
        
        if depth == 0:
            print(self.build_census.__doc__.replace('\t', ' '))
            exit(0)
        
        assert depth > 0 and prebuilt >= 0
        
        # These will store the total running times
        # and the number of words at each stage.
        time_words, time_good, time_census = 0, 0, 0
        num_words, num_good, num_acceptable, num_census = 'SKIPPED', 'SKIPPED', 'SKIPPED', 'SKIPPED'
        
        start = time()
        if self.options.SHOW_PROGRESS: print('Generating words.')
        if prebuilt < 1:
            clean_files(glob(self.options.word_parts.format('*')))
            words, prefixes = self.word_generator.valid_suffixes(self.options.MASTER_PREFIX, self.options.PREFIX_DEPTH, depth)
            if self.options.SHOW_PROGRESS: print('\rTraversing prefix tree: DONE' + ' ' * depth)
            pd.DataFrame({'word': words}).to_csv(self.options.word_parts.format('0'), index=False)
            pd.DataFrame({'word': prefixes}).to_csv(self.options.word_parts.format('prefixes'), index=False)
        
        if prebuilt < 2:
            load_inputs = ifilter(lambda I: not os.path.isfile(self.options.word_parts.format(I[1])), self.get_prefix_blocks(depth))
            
            if self.options.CORES == 1:
                for I in load_inputs:
                    valid_suffixes_map(I)
            else:
                P = Pool(processes=self.options.CORES)
                P.map(valid_suffixes_map, load_inputs)
                P.close()
                P.join()
            
            if self.options.SHOW_PROGRESS: print('\rTraversing word tree: DONE          ')
            
            if self.options.SHOW_PROGRESS: print('Combining files.')
            word_table = pd.concat([pd.read_csv(path) for path in glob(self.options.word_parts.format('*')) if not path.endswith('prefixes.csv')], ignore_index=True)
            word_table.to_csv(self.options.word_file, index=False)
            
            time_words = time() - start
            num_words = len(word_table)
            if self.options.SHOW_TIMINGS: print('Grow time: %fs' % time_words)
            if self.options.SHOW_PROGRESS: print('\t%d possible words to check.' % num_words)
        
        start = time()
        if self.options.SHOW_PROGRESS: print('Collecting properties.')
        if prebuilt < 3:
            clean_files(glob(self.options.good_parts.format('*')))
        
        if prebuilt < 4:
            load_inputs = ifilter(lambda I: not os.path.isfile(self.options.good_parts.format(I[1])), self.get_word_blocks())
            
            if self.options.CORES == 1:
                for I in load_inputs:
                    determine_properties_map(I)
            else:
                P = Pool(processes=self.options.CORES)
                P.map(determine_properties_map, load_inputs)
                P.close()
                P.join()
            
            if self.options.SHOW_PROGRESS: print('\rCollecting properties: DONE          ')
            
            if self.options.SHOW_PROGRESS: print('Combining files.')
            good_table = pd.concat([pd.read_csv(path) for path in glob(self.options.good_parts.format('*'))], ignore_index=True)
            good_table.sort_values('volume', inplace=True)
            good_table.to_csv(self.options.good_file, index=False)
        
            time_good = time() - start
            num_good = good_table.loadable.sum()
            num_acceptable = good_table.acceptable.sum()
            if self.options.SHOW_TIMINGS: print('Load time: %fs' % time_good)
            if self.options.SHOW_PROGRESS: print('\t%d good words.' % num_good)
            if self.options.SHOW_PROGRESS: print('\t%d acceptable words.' % num_acceptable)
        
        start = time()
        if self.options.SHOW_PROGRESS: print('Thinning blocks.')
        
        if prebuilt < 5:
            if self.options.SHOW_PROGRESS: print('Removing duplicates.')
            
            census_table = pd.read_csv(self.options.good_file)
            census_table = census_table[census_table.acceptable]
            census_table = census_table.groupby('isom_sig').apply(lambda df: df[df.key_word == df.key_word.min()])
            census_table.reset_index(inplace=True, drop=True)
            census_table.sort_values('volume', inplace=True)
            census_table.to_csv(self.options.census_file, index=False)
            
            if self.options.SHOW_PROGRESS: print('Thinning: DONE          ')
            
            time_census = time() - start
            num_census = len(census_table)
            if self.options.SHOW_TIMINGS: print('Thin time: %fs' % time_census)
            if self.options.SHOW_PROGRESS: print('\t%d distinct words.' % num_census)
        
        if self.options.SHOW_TIMINGS:
            print('\nSummary:')
            print('\tStatistics:')
            print('\t\tTotal words:\t%s' % num_words)
            print('\t\tGood words:\t%s' % num_good)
            print('\t\tAcceptable words:\t%s' % num_acceptable)
            print('\t\t------------------------------')
            print('\t\tDistinct words:\t%s' % num_census)
            print('\t\t------------------------------')
            print('\tTimings:')
            print('\t\tGrow time:\t%fs' % time_words)
            print('\t\tLoad time:\t%fs' % time_good)
            print('\t\tThin time:\t%fs' % time_census)


# In order to be able to multiprocess these we need to be able to refer
# to various functions globally. Otherwise it would just be
# an instance copy of the function and so lost when the objects are passed
# around by pickling.
def valid_suffixes_map(X):
    self, label, prefix, depth = X
    if self.options.SHOW_PROGRESS: print('\rLoading suffixes of prefix %s' % label)
    
    words, _ = self.word_generator.valid_suffixes(prefix, depth)
    pd.DataFrame({'word': words}).to_csv(self.options.word_parts.format(label), index=False)


def determine_properties_map(X):
    self, label, table = X
    if self.options.SHOW_PROGRESS: print('\rCollecting properties from block: %s' % label)
    
    Properties = namedtuple('Properties', ('word', 'loadable', 'acceptable', 'volume', 'isom_sig', 'homology', 'num_sym', 'ab_sym', 'key_word'))
    Unloadable = lambda word: Properties(word, False, False, 0.0, '', 0, 0, 0, '')
    
    def properties(word):
        ''' Return the properties associated with the mapping class `word`. '''
        word = word.word
        M = self.options.BASE_SURFACE.bundle(monodromy='*'.join(word))
        for i in self.options.MAX_RANDOMIZE_RANGE:  # Try, at most MAX_RANDOMIZE times, to find a solution for M.
            if M.solution_type() =='all tetrahedra positively oriented' : break
            M.randomize()  # There needs to be a better way to do this.
        else:
            return pd.Series(Unloadable(word))  # Couldn't find positive structure.
        G = M.symmetry_group()
        
        return pd.Series(Properties(
            word,
            True,
            self.manifold_filter(self, M),
            float(M.volume()),
            str(M.isometry_signature()),
            str(M.homology()),
            int(G.order()),
            str(G.abelianization()),
            self.ordering.key(word)))
    
    table[list(Properties._fields)] = table.apply(properties, axis=1)
    table.sort_values('volume', inplace=True)
    table.to_csv(self.options.good_parts.format(label), index=False)

