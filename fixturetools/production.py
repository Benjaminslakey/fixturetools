import os
import sys
import functools
import inspect
from copy import deepcopy
from collections import defaultdict

import operator

from fixturetools.utils import get_invocation_id, get_invocation_details
from fixturetools.serialization import fixture_serializer


class FixtureProducer(object):
    def __init__(self, func):
        self._monitored_code = []
        self._invocation_key = None
        self._fixtures = defaultdict(dict)
        self._serializer = fixture_serializer
        self._output_dir = ""

        functools.update_wrapper(self, func)
        self._wrapped_func = func

    @staticmethod
    def reduce(frame, arg):
        raise NotImplementedError("Subclass must implement reduce")

    @staticmethod
    def _merge_fixtures(current_fixtures, previous_fixtures):
        updated_fixtures = None
        if isinstance(previous_fixtures, list):
            updated_fixtures = []
            for item in previous_fixtures + current_fixtures:
                if item in updated_fixtures:
                    continue
                updated_fixtures.append(item)

        elif isinstance(previous_fixtures, dict):
            updated_fixtures = deepcopy(previous_fixtures)
            for k, v in current_fixtures.items():
                updated_fixtures[k] = v
        return updated_fixtures

    def _update_existing_fixtures(self, fixtures_file, current_fixture):
        file_contents = fixtures_file.read()
        fixtures_file.seek(0)
        previous_fixtures = self._serializer.deserialize(file_contents) if file_contents else {}
        new_fixture = self._merge_fixtures(current_fixture, previous_fixtures)
        fixtures_file.write(self._serializer.serialize(new_fixture))
        fixtures_file.truncate()

    def _output_fixtures(self):
        for fixture_name in self._fixtures.keys():
            current_fixture = self._fixtures[fixture_name]
            if self._output_dir:
                fixture_filepath = "%s/%s.%s" % (self._output_dir, fixture_name, self._serializer.file_ext)
                file_exists = os.path.exists(fixture_filepath)
                file_mode = "r+" if file_exists else "w"
                with open(fixture_filepath, file_mode) as fixtures_file:
                    if file_exists:
                        self._update_existing_fixtures(fixtures_file, current_fixture)
                    else:
                        fixtures_file.write(self._serializer.serialize(current_fixture))
            else:
                print(self._serializer.serialize(current_fixture))

    def _create_fixtures(self, frame, arg):
        func_return = self.reduce(frame, arg)
        invocation_id = self._get_invocation_id(frame, arg)
        self._fixtures[frame.f_code.co_name][invocation_id] = arg if func_return is None else func_return

    def _get_invocation_id(self, frame, arg):
        if inspect.isfunction(self._invocation_key):
            return str(self._invocation_key(frame, arg))
        elif isinstance(self._invocation_key, str):
            return self._invocation_key
        else:
            func, func_args, func_kwargs = get_invocation_details(frame)
            return get_invocation_id(func, *func_args, **func_kwargs)

    def _tracer(self, frame, event, arg):
        code_info = (frame.f_code.co_filename, frame.f_code.co_name)
        if event == "return" and code_info in self._monitored_code:
            self._create_fixtures(frame, arg)

    def __call__(self, *args, **kwargs):
        # tracer is activated on next call, return or exception
        previous_profiler = sys.getprofile()
        sys.setprofile(self._tracer)
        try:
            # trace the function call
            res = self._wrapped_func(*args, **kwargs)
        finally:
            # disable tracer and replace with old ones
            sys.setprofile(previous_profiler)
            self._output_fixtures()
        return res


def create_fixtures(monitored_funcs, reducer=None, **kwargs):
    """
    decorator which will monitor execution of the decorated function and produce json fixtures of subsequent calls to the
    functions specified by the only required argument

    :param monitored_funcs: list of functions to monitor invocation of.
        fixtures will be created from these invocations and their results
    :param kwargs: invocation_key: function(frame, arg) which returns a hashable item to use as key for storing function
        results in fixtures the default behavior if not specified is to create an invocation signature to use as the key
    :param kwargs: serializer: a subclass of Serializer. if the results of the specified functions will
        contain objects which are not json serializable this should be a custom class which specifies how to serialize
    :param kwargs: output_dir: path of where to output the created fixtures, if none is given the fixtures will be
        printed to the stdout stream
    :param reducer: optional: function to reduce the size of fixtures to minimum necessary data
    """
    class FixtureDecorator(FixtureProducer):
        def __init__(self, func):
            super(FixtureDecorator, self).__init__(func)
            self._monitored_code = [(f.func_code.co_filename, f.__name__) for f in monitored_funcs] + [(func.func_code.co_filename, func.__name__)]

            # allow kwargs to specify init values for field defined by parent class
            for attr_name in vars(self).keys():
                attr_key = attr_name[1:] if attr_name.startswith("_") else attr_name
                attr_value = kwargs.get(attr_key, None)
                if attr_value:
                    setattr(self, attr_name, attr_value)

        @staticmethod
        def reduce(frame, arg):
            if inspect.isfunction(reducer):
                return reducer(frame, arg)
            return arg
    return FixtureDecorator
