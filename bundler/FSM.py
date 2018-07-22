##### Required modules:
from __future__ import print_function
try:
	from Queue import Queue
except ImportError:
	from queue import Queue
from bundler.extensions import build_c_FSM

# We now use the cFSM class implemented in C++. This is about
# 4 - 6 - 35x faster depending on if you are searching,
# evaluating or looking for cycles.

def word_accepting_FSM(alphabet, acceptable_words):
	''' Given an alphabet and a list of acceptable_words in that alphabet, this
		builds a FSM that returns -1 iff they contain one or more of the
		acceptable_words.
		
		Uses the Aho-Corasick string matching algorithm.
		
		Example: word_accepting_FSM('aAbB', ['ab', 'bb', 'BB']) returns
		a FSM that takes words from the alphabet 'aAbB' and returns -1 iff they
		contain 'ab', 'bb' or 'BB' as a substring. '''
	
	if '' in acceptable_words:
		print('Error: Empty word cannot be acceptable.')
		return
	
	machine = []
	tree = Queue()
	tree.put('')
	all_states = set([''])
	acceptable_words_set = set(acceptable_words)
	acceptable_words_prefixes_set = set(w[:i+1] for w in acceptable_words for i in range(len(w)))
	accepting_states = {}
	
	# Now grow the machine.
	while not tree.empty():
		word = tree.get()
		if any(word[j:] in acceptable_words_set for j in range(len(word))):
			accepting_states[word] = set(word[j:] for j in range(len(word)) if word[j:] in acceptable_words_set)
		
		state = {'':word}
		
		for letter in alphabet:
			state[letter] = ''
			next_word = word + letter
			
			for i in range(len(next_word)-1, -1, -1):
				if next_word[-i-1:] in acceptable_words_prefixes_set:
					state[letter] = next_word[-i-1:]
					
					if state[letter] not in all_states:
						tree.put(state[letter])
						all_states.add(state[letter])
					
					break
		
		machine.append(state)
	
	return build_c_FSM(alphabet, machine, accepting_states)

if __name__ == '__main__':
	M = word_accepting_FSM('aAbBcCxX', ['aaaabac', 'ab', 'aab'])
	print(M.evaluate('abcabCCCxCCXXabBac'))
	for a, b in M.yield_evaluate('abcabCCCxCCXXabBac'):
		print(a, b)
