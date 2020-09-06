
import inspect
from decorator import decorator

def memoize(test=lambda *args, **kwargs: True):
    
    @decorator
    def wraps(function, *args, **kwargs):
        ''' A decorator that memoizes a function. '''
        
        inputs = inspect.getcallargs(function, *args, **kwargs)  # pylint: disable=deprecated-method
        self = inputs.pop('self', function)  # We test whether function is a method by looking for a `self` argument. If not we store the cache in the function itself.
        key = (function.__name__, frozenset(inputs.items()))
        
        try:
            return self._cache[key]
        except AttributeError:
            self._cache = dict()
        except KeyError:
            pass
        
        result = function(*args, **kwargs)
        if test(*args, **kwargs):
            self._cache[key] = result
        
        return result
    
    return wraps

