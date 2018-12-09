##### Required modules:
from __future__ import print_function
import bundler.ordering as ordering
import os
from random import randint
from collections import namedtuple
import pandas as pd
import numpy as np

Properties = namedtuple('Properties', ('isom_sig', 'volume', 'homology', 'num_sym', 'ab_sym'))
Data = namedtuple('Data', ('loadable', 'acceptable', 'word', 'key_word') + Properties._fields)

Unloadable = lambda word, key_word: Data(False, False, word, key_word, '', 0.0, 0, 0, 0)

def properties(M):
    G = M.symmetry_group()
    return Properties(str(M.isometry_signature()), float(M.volume()), str(M.homology()), int(G.order()), str(G.abelianization()))

# Solution types:
ABBREV = {'not attempted' : 'not attempted',
            'all tetrahedra positively oriented' : 'pos',
            'contains negatively oriented tetrahedra' : 'neg',
            'contains flat tetrahedra' : 'flat',
            'contains degenerate tetrahedra' : 'deg',
            'unrecognized solution type' : 'unrec',
            'no solution found' : 'none found'}

class TableGenerator(object):
    def __init__(self, generators, manifold_filter, option):
        self.generators = generators
        self.ordering = ordering.short_lex(generators)
        self.manifold_filter = manifold_filter
        self.option = option
    def __call__(self, words):
        table = pd.DataFrame(index=np.arange(len(words)), columns=Data._fields)
        for index, word in enumerate(words):
            if self.option.SHOW_PROGRESS and not randint(0,self.option.PROGRESS_RATE_LOAD): print('\rLoading: %d / %d.     ' % (index+1, len(words)), end='')
            table.iloc[index] = self.properties(word)
        table.sort_values('volume', inplace=True)
        return Table(self.ordering, self.option, table)
    def properties(self, word):
        M = self.option.BASE_SURFACE.bundle(monodromy='*'.join(word))
        for i in self.option.MAX_RANDOMIZE_RANGE:  # Try, at most MAX_RANDOMIZE times, to find a solution for M.
            if ABBREV[M.solution_type()] == 'pos': break
            M.randomize()  # There needs to be a better way to do this.
        else:
            return Unloadable(word, self.ordering.key(word))  # Couldn't find positive structure.
        
        acceptable = (not self.option.ACCEPTABLE_VOLUMES or any(abs(M.volume() - v) <= self.option.VOLUME_ERROR for v in self.option.ACCEPTABLE_VOLUMES)) and self.manifold_filter(self, M)
        return Data(True, acceptable, word, self.ordering.key(word), *properties(M))

class Table(object):
    def __init__(self, ordering, option, table):
        self.ordering = ordering
        self.option = option
        self.table = table
    
    def to_csv(self, path):
        self.table.to_csv(path, index=False)
    
    def filter_duplicates(self):
        self.table = self.table.groupby('isom_sig').apply(lambda df: df[df.key_word == df.key_word.min()])
        self.table.reset_index(inplace=True, drop=True)
        
        return

    def find(self, M):
        return NotImplemented

