##### Required modules:
from __future__ import print_function
from time import time
import os
import pandas as pd

from bundler.extensions import generate_FSM_info
from generator import load_experiment
#--------------------------------------------------------------

def verify_problem_words(name, n=5):
    ''' Tries to find a solution to all the problem words in the list words
    by checking for reducibility and periodicity in that order. '''
    
    G = load_experiment(name)
    WG = G.word_generator
    
    print('Rebuilding FSM')
    start = time()
    
    seeds = G.options.CURVER_SURFACE.triangulation.edge_curves()
    action = {letter: G.options.CURVER_SURFACE(letter) for letter in WG.MCG_generators}
    advanced_Loop_invariant_FSM = generate_FSM_info(WG.MCG_generators, action, seeds, n)
    # advanced_Loop_invariant_FSM.raise_power(2)
    
    df = pd.read_csv(G.options.good_file)
    words = df[~df.loadable].word
    
    for index, word in enumerate(words):
        print('%d / %d %s' % (index+1, len(words), word), end='')
        
        if advanced_Loop_invariant_FSM.has_cycle(word):  # We also check for up to the 6th power.
            print(' is reducible.')
        elif not WG.valid_word(word):  # Is word really a valid word? Previously max_tree_size != 0.
            print(' is not lex first in its class.')
        else:
            h = G.options.FLIPPER_SURFACE.mapping_class(word)
            if h.is_periodic():
                print(' is periodic.')
            elif h.is_reducible():
                print(' is reducible.')
            else:  # h.is_pseduo_anosov():
                print(' is pseudo-Anosov!!  <---')
    
    print('Running time: %fs.' % (time() - start))

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Generate census')
    parser.add_argument('name', type=str,  help='name of experiment to rerun')
    parser.add_argument('depth', type=int, help='depth to search to')
    args = parser.parse_args()
    verify_problem_words(args.name, args.depth)

