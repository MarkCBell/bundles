from census_generation.fileio import concatinate_files, line_count
import os

rel_path = '../Census/Parts/Word/'
concatinate_files([os.path.join(rel_path, p) for p in os.listdir(rel_path)], '../Census/all_words.txt')

print('Total words:', line_count('../Census/all_words.txt'))