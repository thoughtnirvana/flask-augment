"""
General purpose decorators and other utilities for contract based programming, for the
flask web framework.
"""
import re
from functools import wraps

from flask import request

def _propogate_error(errors, handler=None, exception_type=TypeError):
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
            errors = []
            for arg_name, arg_val, valid in results:
                if not valid:
                    errors.append("'%s = %s' violates constraint %s. "
                                  % (arg_name, arg_val, rules[arg_name]))
            if errors:
                _propogate_error(''.join(errors), error_handler)
            else:
                return fn(*args, **kwargs)
        return wrapper
    return decorator

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
            # `constraint` can either be a regex or a callable.
            validator = constraint
            if not callable(constraint):
                validator = lambda val: re.match(constraint, str(val))
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
            valid_count = len([valid for arg_name, arg_val, valid in results
                                if valid])
            if valid_count < 1:
                error_msg = "One of '%s' must validate. Constraints: %s" % \
                        (rules.keys(), rules)
                _propogate_error(error_msg, error_handler)
            elif valid_count > 1 and exclusive:
                error_msg = "Only one of '%s' must validate. Constraints: %s" % \
                        (rules.keys(), rules)
                _propogate_error(error_msg, error_handler)
            else:
                return fn(*args, **kwargs)
        return wrapper
    return decorator

if __name__ == '__main__':
    import doctest
    doctest.testmod()
