
from __future__ import print_function
from types import SimpleNamespace
import yaml
from collections import namedtuple
from glob import glob
from multiprocessing import Pool
import os
import pandas as pd

from contexttimer import Timer
import snappy
import flipper
import curver

from .word_generators import WordGenerator
from .extensions import ShortLex

def basic_filter(self, x): return True

class Options():
    def __init__(self, **kwargs):
        with open(os.path.join(os.path.dirname(__file__), 'options.yaml')) as stream:
            for key, value in yaml.load(stream, Loader=yaml.CLoader).items():
                setattr(self, key, value)
        
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def __str__(self):
        return '\n'.join('{}: {}'.format(key, value) for key, value in vars(self).items())

class CensusGenerator():
    def __init__(self, surface_name, generators, automorph, MCG_must_contain, word_filter=basic_filter, manifold_filter=basic_filter, options=None):
        self.options = options
        if self.options is None: self.options = Options()
        self.surfaces = SimpleNamespace(
            twister=snappy.twister.Surface(surface_name),
            flipper=flipper.load(surface_name),
            curver=curver.load(surface_name),
            )
        self.generators = generators
        self.automorph = automorph
        self.MCG_must_contain = MCG_must_contain
        self.word_filter = word_filter
        self.manifold_filter = manifold_filter
        self.ordering = ShortLex(self.generators)
    
    def map(self, function, generator):
        if self.options.cores == 1:
            for item in generator:
                function(*item)
        else:
            with Pool(processes=self.options.cores) as P:
                P.starmap(function, generator)  # Consider adding chunksize=
    
    def clean(self, basepath):
        for path in glob(basepath.format('*')):
            os.remove(path)
    
    def build_words(self, depth):
        if self.options.show_progress: print('Generating words.')
        self.word_generator = WordGenerator(self.generators, self.automorph, self.MCG_must_contain, self.word_filter, self.surfaces, self.options)
        
        if not os.path.isfile(self.options.word_parts.format('prefixes')):
            prefixes = valid_suffixes_map(self, '0', self.options.master_prefix, self.options.prefix_depth, depth)
            if self.options.show_progress: print('\rTraversing prefix tree: DONE' + ' ' * depth)
            pd.DataFrame({'word': prefixes}).to_csv(self.options.word_parts.format('prefixes'), index=False)
        
        load_inputs = (
            (self, str(index+1), row.word, depth, None)
            for index, row in pd.read_csv(self.options.word_parts.format('prefixes')).iterrows()
            if not os.path.isfile(self.options.word_parts.format(index+1))
            )
        self.map(valid_suffixes_map, load_inputs)
        
        if self.options.show_progress: print('\rTraversing word tree: DONE          ')
        
        if self.options.show_progress: print('Combining files.')
        word_table = pd.concat([pd.read_csv(path) for path in glob(self.options.word_parts.format('*')) if not path.endswith('prefixes.csv')], ignore_index=True, sort=False)
        word_table.to_csv(self.options.word, index=False)
        
        if self.options.show_progress: print('\t%d possible words to check.' % len(word_table))
    
    def build_properties(self):
        if self.options.show_progress: print('Collecting properties.')
        
        load_inputs = (
            (self, str(index), df)
            for index, df in enumerate(pd.read_csv(self.options.word, chunksize=self.options.chunksize))
            if not os.path.isfile(self.options.properties_parts.format(index))
            )
        self.map(determine_properties_map, load_inputs)
        
        if self.options.show_progress: print('\rCollecting properties: DONE          ')
        
        if self.options.show_progress: print('Combining files.')
        properties_table = pd.concat([pd.read_csv(path) for path in glob(self.options.properties_parts.format('*'))], ignore_index=True, sort=False)
        properties_table.sort_values('volume', inplace=True)
        properties_table.to_csv(self.options.properties, index=False)
        
        if self.options.show_progress: print('\t%d loadable words.' % properties_table.loadable.sum())
        if self.options.show_progress: print('\t%d acceptable words.' % properties_table.acceptable.sum())
    
    def thin_properties(self):
        if self.options.show_progress: print('Removing duplicates.')
        
        census_table = pd.read_csv(self.options.properties)
        census_table = census_table[census_table.acceptable]
        
        census_table['length'] = census_table.word.str.len()
        census_table['canonical'] = census_table.word.str.translate(self.ordering.translate_rule)
        census_table = census_table.sort_values(['isom_sig', 'length', 'canonical']).groupby('isom_sig').first()
        census_table.drop(['length', 'canonical'], axis=1, inplace=True)  # Remove unneeded columns.
        census_table.reset_index(inplace=True, drop=True)
        census_table.sort_values('volume', inplace=True)
        census_table.to_csv(self.options.census, index=False)
        
        if self.options.show_progress: print('Thinning: DONE          ')
        
        if self.options.show_progress: print('\t%d distinct words.' % len(census_table))
    
    def build_census(self, depth, prebuilt=0):
        ''' Builds a census of hyperbolic surface bundles over the circle.
        The census is built to depth 'depth' and we assume that there is a
        prebuilt structure specified by 'prebuilt':
            'prebuilt' == 1 ==> Assumes any existing word blocks are correct,
            'prebuilt' == 2 ==> Assumes word list is complete,
            'prebuilt' == 3 ==> Assumes any existing volume blocks are correct,
            'prebuilt' == 4 ==> Assumes volume list is complete,
        '''
        
        assert depth > 0 and prebuilt >= 0
        
        with Timer() as time_words:
            if prebuilt < 1: self.clean(self.options.word_parts)
            if prebuilt < 2: self.build_words(depth)
            if self.options.show_timings: print('Grow time: %fs' % time_words.elapsed)
        with Timer() as time_properties:
            if prebuilt < 3: self.clean(self.options.properties_parts)
            if prebuilt < 4: self.build_properties()
            if self.options.show_timings: print('Load time: %fs' % time_properties.elapsed)
        with Timer() as time_census:
            if prebuilt < 5: self.thin_properties()
            if self.options.show_timings: print('Thin time: %fs' % time_census.elapsed)
        
        if self.options.show_timings:
            num_words = len(pd.read_csv(self.options.word))
            num_loadable = pd.read_csv(self.options.properties).loadable.sum()
            num_acceptable = pd.read_csv(self.options.properties).acceptable.sum()
            num_census = len(pd.read_csv(self.options.census))
            print('\nSummary:')
            print('\tStatistics:')
            print('\t\tTotal words:\t%s' % num_words)
            print('\t\tLoadable words:\t%s' % num_loadable)
            print('\t\tAcceptable words:\t%s' % num_acceptable)
            print('\t\t------------------------------')
            print('\t\tDistinct words:\t%s' % num_census)
            print('\t\t------------------------------')
            print('\tTimings:')
            print('\t\tGrow time:\t%fs' % time_words.elapsed)
            print('\t\tLoad time:\t%fs' % time_properties.elapsed)
            print('\t\tThin time:\t%fs' % time_census.elapsed)


# In order to be able to multiprocess these we need to be able to refer
# to various functions globally. Otherwise it would just be
# an instance copy of the function and so lost when the objects are passed
# around by pickling.
def valid_suffixes_map(self, label, prefix, depth, word_depth):
    if self.options.show_progress: print('\rLoading suffixes of prefix {} ({})'.format(prefix, label))
    
    words, prefixes = self.word_generator.valid_suffixes(prefix, depth, word_depth)
    pd.DataFrame({'word': words}).to_csv(self.options.word_parts.format(label), index=False)
    
    return prefixes if word_depth is not None else None


def determine_properties_map(self, label, table):
    if self.options.show_progress: print('\rCollecting properties from block: %s' % label)
    
    Properties = namedtuple('Properties', ('loadable', 'acceptable', 'volume', 'isom_sig', 'homology', 'num_sym', 'ab_sym'))
    Unloadable = lambda word: Properties(False, False, 0.0, '', 0, 0, 0)
    
    def properties(row):
        ''' Return the properties associated with the mapping class `word`. '''
        word = row.word
        M = self.surfaces.twister.bundle(monodromy='*'.join(word))
        for i in range(self.options.max_randomize):  # Try, at most MAX_RANDOMIZE times, to find a solution for M.
            if M.solution_type() == 'all tetrahedra positively oriented': break
            M.randomize()  # There needs to be a better way to do this.
        else:
            return pd.Series(Unloadable(word))  # Couldn't find positive structure.
        G = M.symmetry_group()
        
        return pd.Series(Properties(
            True,
            self.manifold_filter(self, M),
            float(M.volume()),
            str(M.isometry_signature()),
            str(M.homology()),
            int(G.order()),
            str(G.abelianization()),
            ))
    
    table[list(Properties._fields)] = table.apply(properties, axis=1)
    table.sort_values('volume', inplace=True)
    table.to_csv(self.options.properties_parts.format(label), index=False)

