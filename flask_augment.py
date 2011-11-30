"""
General purpose decorators and other utilities for contract based programming, for the
flask web framework.
"""
import re
from functools import wraps
from collections import defaultdict

from flask import request

class AugmentError(ValueError):
    """
    Default exception raised when a contraint is voilated.
    """
    def __init__(self, errors):
        self.errors = errors

    def __str__(self):
        """
        Dumps the `self.errors` dictionary.
        """
        return repr(self.errors)

def _propogate_error(errors, handler=None, exception_type=AugmentError):
    """
    Passes the errors to the handler or raises an exception.
    """
    if handler:
        return handler(errors)
    else:
        raise exception_type(errors)

def ensure_args(storage=request.args, error_handler=None, **rules):
    """
    Ensures the value of `arg_name` satisfies `constraint`
    where `rules` is a collection of `arg_name=constraint`.
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            results = _check_args(rules, storage)
            errors = _construct_errors(results, rules)
            if errors:
                plural = 'errors' if len(errors) > 1 else 'error'
                errors['base'].append('%s %s' % (len(errors, plural)))
                _propogate_error(errors, error_handler)
            else:
                return fn(*args, **kwargs)
        return wrapper
    return decorator

def _construct_errors(results, rules):
    """
    Constructs errors dictionary from the returned results.
    """
    errors = defaultdict(list)
    for res in results:
        if len(res) == 4:
            arg_name, arg_val, valid, message = res
        else:
            arg_name, arg_val, valid = res
        if not valid:
            if not message:
                # No user supplied message. Construct a generic message.
                message = '"%s" violates constraint "%s."' % (arg_val, rules[arg_name])
            errors[arg_name].append(message)
    return errors

def _check_args(rules, storage):
    """
    Checks that `arg_val` satisfies `constraint` where `rules` is a
    dicionary of `arg_name=constraint` and `arg_val` is in `kwargs` or `args`
    """
    results = []
    for arg_name, constraint in rules.iteritems():
        # Get the argument value.
        arg_val = storage.get(arg_name)
        if arg_val:
            message = None
            if isinstance(constraint, list) or isinstance(constraint, tuple):
                if len(constraint) == 2:
                    constraint, message = constraint
                else:
                    raise ValueError('Constraints can either be "(constraint, message)" or "constraint"'
                                    '"%s" is in inproper format' % constraint)
            # `constraint` can either be a regex or a callable.
            validator = constraint
            if not callable(constraint):
                validator = lambda val: re.match(constraint, str(val))
            if message:
                results.append((arg_name, arg_val, validator(arg_val), message))
            else:
                results.append((arg_name, arg_val, validator(arg_val)))
    return results

def ensure_one_of(storage=request.args, error_handler=None, exclusive=False, **rules):
    """
    `rules` is a dictionary of `arg_name=1` pairs.
    Ensures at least(or at most depending on `exclusive)` one of `arg_name`
    is passed and not null.
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            results = _check_args(rules, storage)
            errors = _construct_errors(results, rules)
            if errors:
                valid_count = len(rules) - len(errors)
                if valid_count < 1:
                    errors['base'].append('One of constraints must validate.')
                    return _propogate_error(errors, error_handler)
                elif valid_count > 1 and exclusive:
                    errors['base'].append('Only one of constraints should validate.')
                    return _propogate_error(errors, error_handler)
                else:
                    return fn(*args, **kwargs)
            else:
                if exclusive:
                    errors['base'].append('Only one of constraints should validate.')
                    return _propogate_error(errors, error_handler)
                else:
                    return fn(*args, **kwargs)
        return wrapper
    return decorator

if __name__ == '__main__':
    import doctest
    doctest.testmod()
