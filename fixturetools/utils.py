import inspect

from fixturetools.serialization import fixture_serializer


def get_invocation_details(frame):
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


def get_invocation_id(callable_obj, *func_args, **func_kwargs):
    pop_self = False

    if inspect.isfunction(callable_obj):
        callee = callable_obj
    elif callable(callable_obj):
        callee = callable_obj.__call__
        # check if the callable object is an instance of our decorator
        for cls_ in inspect.getmro(callable_obj.__class__):
            if cls_.__name__ == "FixtureProducer":
                pop_self = True
                break
    else:
        TypeError("Cannot generate invocation_id for non-callable object")

    invocation = inspect.getcallargs(callee, *func_args, **func_kwargs)
    # this way using the decorator doesn't pollute the invocation signature of the decorated function
    if pop_self:
        invocation.pop('self')
    return fixture_serializer.serialize(invocation, compact=True)
