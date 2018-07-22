##### Required modules:
import os
import multiprocessing
from snappy.twister import Surface

class options():
	def __init__(self, surface):
		self.surface = surface
		
		# These affect how the script runs.
		self.LARGEST_CLASS = 20			# Largest class of words to generate (0 == all).
		self.LARGEST_CLASS_PREFIX = 50		# Largest class of prefixes to generate (0 == all).
		self.MAX_RANDOMIZE = 50			# The maximum number of times to try and load a manifold.
		self.MULTIPROCESS_GROW = False		# Use multiprocessing in the grow stage?
		self.MULTIPROCESS_LOAD = False		# Use multiprocessing in the load stage?
		self.MULTIPROCESS_THIN = False		# Use multiprocessing in the thin stage?
		self.NUM_PROCESSES = min(40, multiprocessing.cpu_count() // 2)	# Number of processes to spawn (if multiprocessing).
		self.PREFIX_DEPTH = 6				# Length of the prefix blocks.
		self.CHUNKSIZE_LOAD = 500	# How many chunks to hand to each process.
		self.CHUNKSIZE_THIN = 500	# How many chunks to hand to each process.
		self.SUFFIX_DEPTH = 3				# How deep a suffix to precompute.
		# These affect how the script is displayed.
		self.SHOW_TIMINGS = True			# Print out timing data?
		self.SHOW_PROGRESS = True			# Print out record of progress?
		self.SHOW_WARNINGS = False			# Print out warnings.
		self.SHOW_ERRORS = True				# Print out errors.
		self.PROGRESS_RATE_GROW = 100		# How often to update the progress displays.
		self.PROGRESS_RATE_LOAD = 10		# 0 = All, 1 = Less, 2 = Lesser, ..., 100 = Little.
		self.PROGRESS_RATE_THIN = 10		# Warning: Showing progress costs time.
		self.PROGRESS_RATE_VALIDATE = 10	# Warning: Using multiprocessing can corrupt the progress shown.
		
		
		self.FSM_POWER = 2					# Save time by precomputing FSM composed with themselves FSM_power times.
		self.LOOP_INVARIANT_FSM_DEPTH = 4	# How deep to build the machine.
		self.BASIC_SEARCH_RANGE = 50		# How far to search initially.
		self.H_1_CACHE_THRESHOLD = 6		# How much H_1 should we cache?
		
		### Invariant thresholds.
		# If 2 manifold's hyperbolic volumes differ by more than this then they are definitely not isometric. See Jeff's comment in isometry.c (L: 140).
		self.VOLUME_ERROR = 1*10**-2
		self.CHERN_SIMONS_ERROR = 1*10**-2
		self.ACCEPTABLE_VOLUMES = []
		self.ACCEPTABLE_HOMOLOGY_ORDERS = set()  # Acceptable values of |Tor(H_1(M))|.
		
		self.MASTER_PREFIX = ''  # A master prefix to put in front of each word.
		
		### Files and folders:
		# The assumed file structure is: (We will make sure all required folders exist before running.)
		#	working_dir\\
		#		Output\\
		#			Parts\\
		#				Word\\
		#				Good\\
		#				Problem\\
		#				Filtered\\
		#				Census\\
		#			all_words.txt
		#			census.txt
		#			good_words.txt
		#			not_problem_words.txt
		#			problem_words.txt
		#			solutions.txt
		#		bundler\\
		#			extensions\\
		#				c_automorph
		#				c_FSM
		#				c_matrix
		#				__init__.py
		#			__init__.py
		#			Aut_Fn.py
		#			census_generators.py
		#			fat_graphs.py
		#			fileio.py
		#			FSM.py
		#			imultiprocessing.py
		#			options.py
		#			ordering.py
		#			RAAG.py
		#			relators.py
		#			table_generators.py
		#			word_generators.py
		
		# Where everything happens.
		self.working_dir = os.path.normpath(os.path.join(__file__, '..', '..'))
		# -------------------------
		self.census_dir = os.path.join(self.working_dir, 'output')
		self.parts_dir = os.path.join(self.census_dir, 'Parts')
		
		# Where to save parts of the census that have been built.
		self.word_parts_dir = os.path.join(self.parts_dir, 'Word')
		self.good_parts_dir = os.path.join(self.parts_dir, 'Good')
		self.problem_parts_dir = os.path.join(self.parts_dir, 'Problem')
		self.filtered_parts_dir = os.path.join(self.parts_dir, 'Filtered')
		self.census_parts_dir = os.path.join(self.parts_dir, 'Census')
		self.not_problem_parts_dir = os.path.join(self.parts_dir, 'Not_Problem')
		
		self.word_parts = os.path.join(self.word_parts_dir, 'Part.txt')
		self.good_parts = os.path.join(self.good_parts_dir, 'Part.txt')
		self.problem_parts = os.path.join(self.problem_parts_dir, 'Part.txt')
		self.filtered_parts = os.path.join(self.filtered_parts_dir, 'Part.txt')
		self.census_parts = os.path.join(self.census_parts_dir, 'Part.txt')
		self.not_problem_parts = os.path.join(self.not_problem_parts_dir, 'Part.txt')
		
		# Where to output information to.
		self.census_file = os.path.join(self.census_dir, 'census.txt')
		self.problem_file = os.path.join(self.census_dir, 'problem_words.txt')
		self.not_problem_file = os.path.join(self.census_dir, 'not_problem_words.txt')
		self.filtered_file = os.path.join(self.census_dir, 'filtered_words.txt')
		self.good_file = os.path.join(self.census_dir, 'good_words.txt')
		self.word_file = os.path.join(self.census_dir, 'all_words.txt')
		
		# Make any missing directories / files.
		all_directories = [self.census_dir, self.parts_dir, self.word_parts_dir, self.good_parts_dir, self.problem_parts_dir, self.filtered_parts_dir, self.not_problem_parts_dir, self.census_parts_dir]
		all_files = [self.word_file, self.good_file, self.problem_file, self.filtered_file, self.not_problem_file, self.census_file]
		for path in all_directories:
			if not os.path.exists(path):
				os.makedirs(path)
		for path in all_files:
			if not os.path.isfile(path):
				open(path, 'w')
		
		self.BASE_SURFACE = Surface(self.surface)
		self.SURFACE_FILE_CONTENTS = self.BASE_SURFACE.surface_contents
		if self.SHOW_PROGRESS: print('Surface set:\n%s' % self.BASE_SURFACE.info())
		self.MAX_RANDOMIZE_RANGE = range(self.MAX_RANDOMIZE)
		self.VOLUME_ROUND = min(n for n in range(10) if 10**-n < self.VOLUME_ERROR)
	
	def tidy(self):
		''' If you make any changes to the options after initialisation then call this to optimise and tidy up the parameters set. '''
		self.ACCEPTABLE_VOLUMES = sorted(self.ACCEPTABLE_VOLUMES)
		self.ACCEPTABLE_HOMOLOGY_ORDERS = set(self.ACCEPTABLE_HOMOLOGY_ORDERS)  # Acceptable values of |Tor(H_1(M))|.

