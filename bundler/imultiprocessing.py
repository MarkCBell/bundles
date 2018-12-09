##### Required modules:
from multiprocessing import Process
from multiprocessing import JoinableQueue as Queue

def _worker_thread(jobs, answers=None):
    # Takes work of the form (func, data) from the jobs queue and computes:
    #     result = func(data)
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

