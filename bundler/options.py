
import os
import multiprocessing
from snappy.twister import Surface

class Options():
    def __init__(self, surface):
        self.surface = surface
        
        # These affect how the script runs.
        self.LARGEST_CLASS = 20  # Largest class of words to generate (0 == all).
        self.LARGEST_CLASS_PREFIX = 50  # Largest class of prefixes to generate (0 == all).
        self.MAX_RANDOMIZE = 50  # The maximum number of times to try and load a manifold.
        self.CORES = 1  # Number of processes to spawn (if multiprocessing).
        self.PREFIX_DEPTH = 6  # Length of the prefix blocks.
        self.CHUNKSIZE_LOAD = 500  # How many chunks to hand to each process.
        self.CHUNKSIZE_THIN = 500  # How many chunks to hand to each process.
        self.SUFFIX_DEPTH = 3  # How deep a suffix to precompute.
        # These affect how the script is displayed.
        self.SHOW_TIMINGS = True  # Print out timing data?
        self.SHOW_ERRORS = True  # Print out errors.
        self.SHOW_WARNINGS = False  # Print out warnings.
        self.SHOW_PROGRESS = True  # Print out record of progress?
        self.PROGRESS_RATE_GROW = 100  # How often to update the progress displays.
        self.PROGRESS_RATE_LOAD = 10  # 0 = All, 1 = Less, 2 = Lesser, ..., 100 = Little.
        
        self.FSM_POWER = 2  # Save time by precomputing FSM composed with themselves FSM_power times.
        self.LOOP_INVARIANT_FSM_DEPTH = 4  # How deep to build the machine.
        self.BASIC_SEARCH_RANGE = 50  # How far to search initially.
        self.H_1_CACHE_THRESHOLD = 6  # How much H_1 should we cache?
        
        ### Invariant thresholds.
        # If 2 manifold's hyperbolic volumes differ by more than this then they are definitely not isometric. See Jeff's comment in isometry.c (L: 140).
        self.VOLUME_ERROR = 1*10**-2
        self.CHERN_SIMONS_ERROR = 1*10**-2
        self.ACCEPTABLE_HOMOLOGY_ORDERS = set()  # Acceptable values of |Tor(H_1(M))|.
        
        self.MASTER_PREFIX = ''  # A master prefix to put in front of each word.
        
        ### Files and folders:
        # The assumed file structure is: (We will make sure all required folders exist before running.)
        #    working_dir\\
        #        output\\
        #            parts\\
        #                word{}.csv
        #                good{}.csv
        #            words.csv
        #            good.csv
        #            census.csv
        
        # Where everything happens.
        self.working_dir = '.'
        # -------------------------
        self.census_dir = os.path.join(self.working_dir, 'output')
        self.parts_dir = os.path.join(self.census_dir, 'parts')
        
        # Where to save parts of the census that have been built.
        self.word_parts = os.path.join(self.parts_dir, 'word{}.csv')
        self.good_parts = os.path.join(self.parts_dir, 'good{}.csv')
        
        # Where to output information to.
        self.census_file = os.path.join(self.census_dir, 'census.csv')
        self.good_file = os.path.join(self.census_dir, 'good.csv')
        self.word_file = os.path.join(self.census_dir, 'words.csv')
        
        # Make any missing directories / files.
        all_directories = [self.census_dir, self.parts_dir]
        all_files = [self.word_file, self.good_file, self.census_file]
        for path in all_directories:
            if not os.path.exists(path):
                os.makedirs(path)
        for path in all_files:
            if not os.path.isfile(path):
                open(path, 'w').close()
        
        self.BASE_SURFACE = Surface(self.surface)
        self.SURFACE_FILE_CONTENTS = self.BASE_SURFACE.surface_contents
        if self.SHOW_PROGRESS: print('Surface set:\n%s' % self.BASE_SURFACE.info())
        self.MAX_RANDOMIZE_RANGE = range(self.MAX_RANDOMIZE)
        self.VOLUME_ROUND = min(n for n in range(10) if 10**-n < self.VOLUME_ERROR)

