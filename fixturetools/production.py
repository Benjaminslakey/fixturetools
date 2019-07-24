import functools
import inspect
import sys
from copy import deepcopy
from collections import defaultdict

from fixturetools.utils import get_invocation_id
from fixturetools.serialization import fixture_serializer


class FixtureProducer(object):
    def __init__(self, func):
        self._func_names = []
        self._serializer = fixture_serializer
        self._output_dir = ""
        self._fixtures = defaultdict(dict)

        functools.update_wrapper(self, func)
        self._wrapped_func = func

    @staticmethod
    def _get_func_details(frame):
        arg_info = inspect.getargvalues(frame)
        frame_variables = arg_info.locals.copy()

        func_kwargs = frame_variables.get(arg_info.keywords, {})
        # create positional args array using named parameters first, then varargs
        varargs = frame_variables.get(arg_info.varargs, [])
        func_args = []
        for arg_name in arg_info.args:
            arg_value = frame_variables.get(arg_name)
            func_args.append(arg_value)
        for arg_value in varargs:
            func_args.append(arg_value)

        module = inspect.getmodule(frame.f_code, _filename=frame.f_code.co_filename)
        obj = getattr(module, frame.f_code.co_name)

        if callable(obj):
            return obj, func_args, func_kwargs
        else:
            raise ValueError(
                "Could not fetch function details for -- %s: type=%s" % (
                    getattr(obj, '__name__', default="Unknown"), type(obj)
                )
            )

    @staticmethod
    def reduce(frame, arg):
        raise NotImplementedError("Subclass must implement reduce")

    @staticmethod
    def _update_existing_fixtures(current_fixtures, previous_fixtures):
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

    def _create_fixtures(self, frame, arg):
        func_return = self.reduce(frame, arg)
        func, func_args, func_kwargs = self._get_func_details(frame)
        invocation_id = get_invocation_id(func, *func_args, **func_kwargs)
        self._fixtures[frame.f_code.co_name][invocation_id] = arg if func_return is None else func_return

    def _output_fixtures(self):
        for fixture_name in self._fixtures.keys():
            current_fixture = self._fixtures[fixture_name]
            if self._output_dir:
                fixture_filepath = "%s/%s.%s" % (self._output_dir, fixture_name, self._serializer.file_ext)
                with open(fixture_filepath, 'r+') as fixtures_file:
                    file_contents = fixtures_file.read()
                    fixtures_file.seek(0)

                    previous_fixtures = self._serializer.deserialize(file_contents) if file_contents else {}
                    new_fixture = self._update_existing_fixtures(current_fixture, previous_fixtures)

                    fixtures_file.write(self._serializer.serialize(new_fixture))
                    fixtures_file.truncate()

            else:
                print(self._serializer.serialize(current_fixture))

    def _tracer(self, frame, event, arg):
        func_name = frame.f_code.co_name
        if event == "return" and (func_name in self._func_names or func_name == self._wrapped_func.__name__):
            self._create_fixtures(frame, arg)

    def __call__(self, *args, **kwargs):
        # tracer is activated on next call, return or exception
        sys.setprofile(self._tracer)
        try:
            # trace the function call
            res = self._wrapped_func(*args, **kwargs)
        finally:
            # disable tracer and replace with old one
            sys.setprofile(None)
        self._output_fixtures()
        return res


def create_fixtures(func_names, reducer=None, **kwargs):
    """
    decorator which will monitor execution of the decorated function and produce json fixtures of subsequent calls to the
    functions specified by the only required argument

    :param func_names: list of function names to monitor invocation of.
        fixtures will be created from these invocations and their results
    :param kwargs: serializer: a subclass of Serializer. if the results of the specified functions will
        contain objects which are not json serializable this should be a custom class which specifies how to serialize
    :param kwargs: output_dir: path of where to output the created fixtures, if none is given the fixtures will be
        printed to the stdout stream
    :param reducer: optional: function to reduce the size of fixtures to minimum necessary data
    """
    class FixtureDecorator(FixtureProducer):
        def __init__(self, func):
            super(FixtureDecorator, self).__init__(func)
            self._func_names = func_names

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
