##### Required modules:
from __future__ import print_function
import bundler.ordering as ordering
import os
from random import randint
from collections import namedtuple
import pandas as pd

EXACT = ['homology', 'num_sym', 'ab_sym']
Properties = namedtuple('Properties', ('volume', 'homology', 'num_sym', 'ab_sym'))
Data = namedtuple('Data', ('loadable', 'acceptable') + Properties._fields)

UNLOADABLE = Data(False, False, 0.0, 0, 0, 0)

def properties(M):
    G = M.symmetry_group()
    return Properties(float(M.volume()), str(M.homology()), int(G.order()), str(G.abelianization()))

def properties_match(self, p1, p2):
    if abs(p1.volume - p2.volume) > self.option.VOLUME_ERROR: False
    if p1[EXACT] != p2[EXACT]: return False
    
    return True

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
        table = pd.DataFrame(columns=Data._fields)
        for index, word in enumerate(words):
            if self.option.SHOW_PROGRESS and not randint(0,self.option.PROGRESS_RATE_LOAD): print('\rLoading: %d / %d.     ' % (index+1, len(words)), end='')
            table.loc[word] = self.properties(word)
        return Table(self.ordering, self.option, table)
    def properties(self, word):
        M = self.option.BASE_SURFACE.bundle(monodromy='*'.join(word))
        for i in self.option.MAX_RANDOMIZE_RANGE:  # Try, at most MAX_RANDOMIZE times, to find a solution for M.
            if ABBREV[M.solution_type()] == 'pos': break
            M.randomize()  # There needs to be a better way to do this.
        else:
            return UNLOADABLE  # Couldn't find positive structure.
        
        acceptable = (not self.option.ACCEPTABLE_VOLUMES or any(abs(M.volume() - v) <= self.option.VOLUME_ERROR for v in self.option.ACCEPTABLE_VOLUMES)) and self.manifold_filter(self, M)
        return Data(True, acceptable, *properties(M))

class Table(object):
    def __init__(self, ordering, option, table):
        self.ordering = ordering
        self.option = option
        self.table = table
        self.table.sort_values('volume', inplace=True)
    
    def to_csv(self, path):
        self.table.to_csv(path, index_label='word')
    
    def isometry_test(self, m, n):
        M = self.option.BASE_SURFACE.bundle(monodromy='*'.join(m)) if isinstance(m, str) else m
        N = self.option.BASE_SURFACE.bundle(monodromy='*'.join(n)) if isinstance(n, str) else n
        for i in range(1):
            if M.is_isometric_to(N):
                return True
            # M.randomize()
            # N.randomize()
        
        return False
    
    def filter_duplicates(self):
        ''' None's out rows of the table to leave one representative of each isotopy class.
        Assumes that each line of the table given to it is in the format
            [word, manifold_object, volume, homology...] '''
        if self.option.SHOW_PROGRESS: print('Thinning table.')
        
        for i in range(len(self.table)):
            if self.option.SHOW_PROGRESS and not randint(0, self.option.PROGRESS_RATE_THIN): print('\rThinning: %d / %d.     ' % (i, len(self.table)), end='')
            RI = self.table.iloc[i]
            
            for j in range(i-1,-1,-1):  # Quadratic here, but this is usually small (< 10). - Ha! In the S_1_2 13 census volume buckets were ~2900.
                RJ = self.table.iloc[j]
                if not RJ.acceptable: continue
                
                if abs(RI.volume - RJ.volume) > self.option.VOLUME_ERROR: break  # Skip if the hyp. volumes aren't the same.
                if not properties_match(self, RI, RJ): continue
                
                try:
                    if self.isometry_test(RI.name, RJ.name):  # Want to avoid this if at all possible.
                        self.table.loc[RJ.name if self.ordering(RI.name, RJ.name) else RI.name, 'acceptable'] = False
                        break
                except:
                    if self.option.SHOW_WARNINGS: print('%s ?~ %s' % (RI.name, RJ.name))
        
        if self.option.SHOW_PROGRESS: print('\rThinning: DONE           ')
        return

    def find(self, M):
        ''' Return the index of M in self. '''
        p = properties(M)
        
        low = self.table.volume.searchsorted(p.volume - self.option.VOLUME_ERROR)
        high = self.table.volume.searchsorted(p.volume + self.option.VOLUME_ERROR, side='right')
        
        for i in range(low, high):
            RI = self.table.iloc[i]
            try:
                if properties_match(p, RI):
                    if self.isometry_test(RI.name, M):
                        return i
            except:
                print('Error with %s' % table[i][0])
        
        return -1

