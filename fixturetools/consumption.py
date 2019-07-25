import inspect
from functools import partial

from fixturetools.serialization import fixture_serializer
from fixturetools.utils import get_invocation_id


def get_results_table(fixture_filepath, serializer=fixture_serializer):
    with open(fixture_filepath) as f:
        file_contents = f.read()
    function_results_table = serializer.deserialize(file_contents)
    return function_results_table


def str_lookup(results_table, lookup_key):
    return results_table.get(lookup_key, None)


def invocation_lookup(results_table, func, *func_args, **func_kwargs):
    invocation_id = get_invocation_id(func, *func_args, **func_kwargs)
    return results_table.get(invocation_id, None)


def double_factory(fixture_filepath, func_to_double=None, serializer=fixture_serializer):
    function_results_table = get_results_table(fixture_filepath, serializer=serializer)
    if inspect.isfunction(func_to_double):
        double = partial(invocation_lookup, function_results_table, func_to_double)
    else:
        double = partial(str_lookup, function_results_table)
    return double
