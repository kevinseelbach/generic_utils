"""
Module which provides utilities for helping with writing, using and generally dealing with python decorators
"""


def decorator(func):
    """Decorator which is used to decorate a function which is to be used as a decorator for other functions.  The
    primary thing this decorator does is to provide support for defining decorators which take args or do not take
    args through the same standard function signature.  For instance, decorators can be used in two ways ::

        @mydecorator
        def some_func():
            pass

    or ::

        @mydecorator()
        def some_func():
            pass

    In this scenario mydecorator would have to be defined in a way which would handle both cases which can be error
    prone and painful.  Instead, if the @decorator decorator is used then the signature is easy and consistent ::

        @decorator
        def mydecorator(func, *args, **kwargs):
            pass

    """
    decorator_args = {
        "args": [],
        "kwargs": {}
    }

    def decorator_proxy(*args, **kwargs):
        """Method which handles the difference between a call to the decorator with or without arguments and proxies
        it down to the underlying decorator function
        """
        if args and callable(args[0]):
            # Decorating the actual function, so call down to the real decorator function with the target func to
            # decorate as well as the *args and **kwargs
            target_func = args[0]
            return func(target_func, *decorator_args["args"], **decorator_args["kwargs"])
        else:
            # Decorator called with args, so store them off to be passed down when decorating the actual function
            decorator_args["args"] = args
            decorator_args["kwargs"] = kwargs
            return decorator_proxy

    return decorator_proxy
