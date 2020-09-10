
from collections import namedtuple
from glob import glob
from multiprocessing import Pool
from types import SimpleNamespace
import os
import pandas as pd

from contexttimer import Timer
import snappy
import flipper
import curver

from .word_generator import WordGenerator

def basic_filter(self, x): return True

class Options():
    def __init__(self, **kwargs):
        self.cores = 1
        self.prefix_depth = 6
        self.chunksize = 500
        self.suffix_depth = 3
        self.fsm_power = 2
        self.loop_invariant_fsm_depth = 4

        # These affect how the script is displayed.
        self.show_progress = True
        self.show_timings = True
        self.progress_rate = 100
        self.log_level = 'info'

        # File structure.
        self.word_parts = './output/parts/word_{}.csv'
        self.properties_parts = './output/parts/prop_{}.csv'
        self.word = './output/words.csv'
        self.properties = './output/prop.csv'
        self.census = './output/census.csv'

        # The affect what the script computes.
        self.master_prefix = ''
        self.max_randomize = 50
        self.largest_class = 20
        self.largest_class_prefix = 50
        self.basic_search_range = 50
        
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def __str__(self):
        return '\n'.join('{}: {}'.format(key, value) for key, value in vars(self).items())

class CensusGenerator():
    def __init__(self, surface_name, generators, automorph, MCG_must_contain, word_filter=basic_filter, manifold_filter=basic_filter, options=None):
        self.surface_name = surface_name
        self.generators = generators
        self.automorph = automorph
        self.MCG_must_contain = MCG_must_contain
        self.word_filter = word_filter
        self.manifold_filter = manifold_filter
        self.options = options if options is not None else Options()
        
        self.surfaces = SimpleNamespace(
            twister=snappy.twister.Surface(self.surface_name),
            flipper=flipper.load(self.surface_name),
            curver=curver.load(self.surface_name),
            )
        self.word_generator = WordGenerator(self.generators, self.automorph, self.MCG_must_contain, self.word_filter, self.surfaces, self.options)
    
    def map(self, function, generator):
        if self.options.cores == 1:
            for item in generator:
                function(*item)
        else:
            with Pool(processes=self.options.cores) as P:
                P.starmap(function, generator)  # Consider adding chunksize=
    
    @staticmethod
    def clean(basepath):
        for path in glob(basepath.format('*')):
            os.remove(path)
    
    def build_words(self, depth):
        if self.options.show_progress: print('Generating words.')
        
        if not os.path.isfile(self.options.word_parts.format('prefixes')):
            prefixes = valid_suffixes_map(self, '0', self.options.master_prefix, self.options.prefix_depth, depth)
            if self.options.show_progress: print('\rTraversing prefix tree: DONE' + ' ' * depth)
            if self.options.show_progress: print('{} prefixes to explore'.format(len(prefixes)))
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
        
        if self.options.show_progress: print('\tWords {}'.format(len(word_table)))
    
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
        
        if self.options.show_progress: print('\tHyperbolic {}'.format(properties_table.hyperbolic.sum()))
        if self.options.show_progress: print('\tLoadable {}'.format(properties_table.loadable.sum()))
        if self.options.show_progress: print('\tAcceptable {}'.format(properties_table.acceptable.sum()))
    
    def thin_properties(self):
        if self.options.show_progress: print('Removing duplicates.')
        
        census_table = pd.read_csv(self.options.properties)
        census_table = census_table[census_table.acceptable]
        
        census_table['length'] = census_table.word.str.len()
        census_table['canonical'] = census_table.word.apply(self.word_generator.repr_word)
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
            words = pd.read_csv(self.options.word)
            properties = pd.read_csv(self.options.properties)
            census = pd.read_csv(self.options.census)
            print('\nSummary:')
            print('\tStatistics:')
            print('\t\tWords:\t{}'.format(len(words)))
            print('\t\tHyperbolic:\t{}'.format(properties.hyperbolic.sum()))
            print('\t\tLoadable:\t{}'.format(properties.loadable.sum()))
            print('\t\tAcceptable:\t{}'.format(properties.acceptable.sum()))
            print('\t\t------------------------------')
            print('\t\tDistinct:\t{}'.format(len(census)))
            print('\t\t------------------------------')
            print('\tTimings:')
            print('\t\tGrow time:\t{:0.2f}s'.format(time_words.elapsed))
            print('\t\tLoad time:\t{:0.2f}s'.format(time_properties.elapsed))
            print('\t\tThin time:\t{:0.2f}s'.format(time_census.elapsed))


# In order to be able to multiprocess these we need to be able to refer
# to various functions globally. Otherwise it would just be
# an instance copy of the function and so lost when the objects are passed
# around by pickling.

def valid_suffixes_map(self, label, prefix, depth, word_depth):
    if self.options.show_progress: print('\rLoading suffixes of prefix {} ({})'.format(prefix, label))
    
    words, prefixes = self.word_generator.valid_suffixes(prefix, depth, word_depth)
    pd.DataFrame({'word': words}).to_csv(self.options.word_parts.format(label), index=False)
    
    return prefixes

def determine_properties_map(self, label, table):
    if self.options.show_progress: print('\rCollecting properties from block: %s' % label)
    
    Properties = namedtuple('Properties', ('hyperbolic', 'loadable', 'acceptable', 'volume', 'isom_sig', 'homology', 'num_sym', 'ab_sym'))
    Unloadable = lambda is_hyperbolic: Properties(is_hyperbolic, False, False, 0.0, '', 0, 0, 0)
    
    def properties(row):
        ''' Return the properties associated with the mapping class `word`. '''
        word = row.word
        M = self.surfaces.twister.bundle(monodromy='*'.join(word))
        for _ in range(self.options.max_randomize):  # Try, at most MAX_RANDOMIZE times, to find a solution for M.
            if M.solution_type() == 'all tetrahedra positively oriented': break
            M.randomize()  # There needs to be a better way to do this.
        else:  # Couldn't find positive structure.
            return pd.Series(Unloadable(self.surfaces.flipper(word).is_pseudo_anosov()))
        
        G = M.symmetry_group()
        return pd.Series(Properties(
            True,
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

