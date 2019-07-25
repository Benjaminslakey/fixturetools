import inspect

from fixturetools.production import FixtureProducer
from fixturetools.serialization import fixture_serializer


def get_invocation_id(callable_obj, *func_args, **func_kwargs):
    # we don't want the
    pop_self = False

    if inspect.isfunction(callable_obj):
        callee = callable_obj
    elif callable(callable_obj):
        callee = callable_obj.__call__
        pop_self = isinstance(callable_obj, FixtureProducer)
    else:
        TypeError("Cannot generate invocation id for non-callable object")

    invocation = inspect.getcallargs(callee, *func_args, **func_kwargs)
    # this way using the decorator doesn't pollute the invocation signature of the decorated function
    if pop_self:
        invocation.pop('self')
    return fixture_serializer.serialize(invocation, compact=True)
