from collections import namedtuple
from functools import partial

from mockito.invocation import Invocation

from src.serialization import JSONSerializer, fixture_serializer


def get_invocation_id(func, *func_args, **func_kwargs):
    FakeMock = namedtuple('FakeMock', 'strict')
    fake_mock = FakeMock(strict=False)
    invocation = Invocation(fake_mock, func.__name__)
    invocation._remember_params(func_args, func_kwargs)
    return str(invocation)


def result_lookup(func, invocation_table, *func_args, **func_kwargs):
    invocation_id = get_invocation_id(func, *func_args, **func_kwargs)
    return invocation_table[invocation_id]


def create_function_double(original_function, fixture_filepath, serializer=fixture_serializer):
    with open(fixture_filepath) as f:
        file_contents = f.read()
        function_invocation_table = serializer.deserialize(file_contents)
    return partial(result_lookup, original_function, function_invocation_table)
