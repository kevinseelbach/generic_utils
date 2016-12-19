
class FactoryMemoizer(object):
    """
    Helper class which allows for wrapping a Factory and memoizing inputs into the
     constructor/build/create methods.
    """

    def __init__(self, factory, **kwargs):
        self.factory = factory
        self.kwargs = kwargs
        super(FactoryMemoizer, self).__init__()

    def __call__(self, *args, **kwargs):
        final_kwargs = {}
        # The order is important here.  The expectation is that a memoized value should be overridden by a specific arg
        # passed into the underlying Factory instantiation
        final_kwargs.update(self.kwargs)
        final_kwargs.update(kwargs)

        return self.factory(*args, **final_kwargs)
