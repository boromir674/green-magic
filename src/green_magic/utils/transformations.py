import abc
import inspect
import types
from functools import wraps

__all__ = ['Transformer']

class TransformerInterface(abc.ABC):
    """The interface defining a method to transform structured data. Anyone, implementing this has the ability to receive
    some kind of data and return some kind of transformed version of them.
    """
    @abc.abstractmethod
    def transform(self, data, **kwargs):
        """Takes data and optional keyword arguments and transforms them.
        Input data can represent either a single variable of an observations (scalar)
        or a vector of observations of the same variable.

        Example 1:
        obs1 = [x1, y1, z1]
        fa = f_a(x)
        fb = f_b(x)
        fc = f_c(x)
        feature_vector1 = [fa(x1), fb(y1), fc(z1)]

        So, each of fa, fb and fc can implement the Transformer interface.

        Example 2:
        obs1 = [x1, y1, z1]
        obs2 = [x2, y2, z2]
        obs3 = [x3, y3, z3]
        obs4 = [x4, y4, z4]
        data = [obs1;
                obs2;
                obs3;
                obs4]  shape = (4,3)
        fa = f_a(x)
        fb = f_b(x)
        fc = f_c(x)
        feature_vectors = [fa(data[:0], fb(data[:1], fc(data[:2])]  - shape = (4,3)

        Again each of fa, fb and fc can implement the Transformer interface.

        Args:
            data (object): the input data to transform; the x in an f(x) invocation

        Raises:
            NotImplementedError: [description]
        """
        raise NotImplementedError


class RuntimeTransformer(TransformerInterface, abc.ABC):
    """Examines whether the input object is callable, if it can receive at least one input argument and also
    whether it can accept kwargs. Depending on the kwargs check, "configures" the '_transform' method to process
     any kwargs at runtime or to ignore them.

    Args:
        a_callable (callable): a callable object that can be potentially used to delegate the transformation operation
    """
    def __new__(cls, *args, **kwargs):
        x = super().__new__(cls)
        a_callable = args[0]
        if not callable(a_callable):
            raise ValueError(f"Expected a callable as argument; instead got '{type(a_callable)}'")
        nb_mandatory_arguments = a_callable.__code__.co_argcount  # this counts sums both *args and **kwargs
        # use syntax like 'def a(b, *, c=1, d=2): .. to separate pos args from kwargs and to inform 'inspect' lib about it
        if nb_mandatory_arguments < 1:
            raise ValueError(f"Expected a callable that receives at least one positional argument; instead got a callable that "
                             f"receives '{nb_mandatory_arguments}'")
        signature = inspect.signature(a_callable)
        parameters = [param for param in signature.parameters.values()]

        if 1 < nb_mandatory_arguments:
            def _transform(self, data, **keyword_args):
                return a_callable(data, **keyword_args)
            x._transform = types.MethodType(_transform, x)
        elif nb_mandatory_arguments == len(parameters):
            def _transform(self, data, **keyword_args):
                return a_callable(data)
            x._transform = types.MethodType(_transform, x)
        else:
            raise Exception("Something went really bad. Check code above.")
        x._callable = a_callable
        return x


class Transformer(RuntimeTransformer):
    """Delegates all the transformation operation to its '_transform' method provided by its '_callable' field."""
    def transform(self, data, **kwargs):
        return self._transform(data, **kwargs)


def my_decorator(a_callable):
    @wraps(a_callable)
    def wrapper(*args, **kwds):
        print('Calling decorated function')
        return a_callable(*args, **kwds)
    return wrapper


if __name__ == '__main__':
    tr1 = Transformer(lambda x: x + 1)
    inp = 10
    out = tr1.transform(inp)
    assert 11 == out

    def gg(a, b=2):
        return a*b + 1
    tr1 = Transformer(gg)
    inp = 10
    out = tr1.transform(inp)
    assert 21 == out
    out = tr1.transform(inp, b=3)
    assert 31 == out