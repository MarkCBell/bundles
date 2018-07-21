##### Required modules:
from multiprocessing import Process
from multiprocessing import JoinableQueue as Queue

def _worker_thread(jobs, answers=None):
	# Takes work of the form (func, data) from the jobs queue and computes:
	# 	result = func(data)
	# If an answers queue is also provided then the result is placed back there.
	
	while True:
		index, func, data = jobs.get()
		result = func(data)  # What if an error occurs?
		
		if answers is not None: answers.put((index, result))
		jobs.task_done()

def imap(function, iterable, num_workers=1, return_results=True):
	''' Uses a number of worker threads to apply function to each element 
	of iterable and return the results as a list if requested.
	
	Importantly, unlike multiprocessing.Pool.map, this will work on iterables
	without having to do iterable = list(iterable) first. '''
	
	jobs = Queue(4 * num_workers)
	answers = Queue(jobs._maxsize) if return_results else None
	
	try:  # Create and start some workers.
		workers = [Process(target=_worker_thread, args=(jobs, answers)) for i in range(num_workers)]
		for worker in workers: 
			worker.daemon = True
			worker.start()
	except ValueError:
		for worker in workers: worker.terminate()
		raise ValueError
	
	if return_results:
		results = []
		
		job_number = -1
		for job_number, item in enumerate(iterable):
			jobs.put((job_number, function, item))
			
			if job_number >= answers._maxsize:
				index, ans = answers.get()
				if index >= len(results): results += [None] * (index + 1 - len(results))
				results[index] = ans
		jobs.join()
		
		# Collect up the outstanding answers.
		for i in range(min(job_number+1, answers._maxsize)):
			index, ans = answers.get()
			if index >= len(results): results += [None] * (index + 1 - len(results))
			results[index] = ans
		
		for worker in workers: worker.terminate()
		return results
	else:
		for job_number, item in enumerate(iterable):
			jobs.put((job_number, function, item))
		jobs.join()
		
		for worker in workers: worker.terminate()
		return None

def test_f(x): return x+7
def test_g(x): return 2*x + 1
def test_h(x): return x

def test():
	# Some basic checks, a lot of the time imap should be the same as map.
	assert imap(test_f, range(10)) == list(map(test_f, range(10)))
	assert imap(test_f, range(10), num_workers=4) == list(map(test_f, range(10)))
	assert imap(test_g, imap(test_f, range(1000), num_workers=4), num_workers=4) == list(map(test_g, map(test_f, range(1000))))
	assert imap(test_f, []) == []
	assert imap(test_g, [], num_workers=4) == []
	
	assert len(imap(test_h, range(10000), num_workers=4)) == 10000
	
	# We can also call functions for which we expect no feedback.
	assert imap(test_h, range(10000), num_workers=4, return_results=False) is None
	
	# What happens if functon(item) throws an error?
	assert imap(test_f, [1,2,4,None,7,1,2], num_workers=1) == [8,9,11,None,14,8,9]
	
	return True

if __name__ == '__main__': print(test())
