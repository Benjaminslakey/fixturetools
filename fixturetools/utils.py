import inspect

from fixturetools.serialization import fixture_serializer


def get_invocation_id(func, *func_args, **func_kwargs):
    invocation = inspect.getcallargs(func, *func_args, **func_kwargs)
    return fixture_serializer.serialize(invocation)
