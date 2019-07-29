import cPickle
import inspect
from json import JSONEncoder, JSONDecoder
from datetime import datetime
import dateutil.parser


CLASS_TYPE_ATTR = '__cls_type__'
DT_TYPE_ATTR = 'dt_string'
CPICKLE_DUMP_ATTR = 'cpickle_dump'


class Serializer(object):
    def serialize(self, *args, **kwargs):
        raise NotImplementedError("Subclass must implement serialize")

    def deserialize(self, *args, **kwargs):
        raise NotImplementedError("Subclass must implement deserialize")

    @property
    def file_ext(self):
        return getattr(self, "_file_ext", "")


class JSONSerializer(Serializer):
    def __init__(self, encoder=None, decoder=None, indent=2):
        self._file_ext = "json"
        self._encoder = encoder if isinstance(encoder, JSONEncoder) else JSONEncoder()
        self._decoder = decoder if isinstance(decoder, JSONDecoder) else JSONDecoder()
        self._indent = indent

    def serialize(self, obj, output_format=None, **kwargs):
        self._encoder.indent = None if kwargs.get('compact', False) else self._indent
        result = self._encoder.encode(obj)
        self._encoder.indent = self._indent
        return result

    def deserialize(self, json_string, **kwargs):
        return self._decoder.decode(json_string)


def add_hooks(obj_instance, custom_hooks=None):
    hooks = [] if custom_hooks is None else custom_hooks
    try:
        for cls_, hook in hooks:
            obj_instance.add_custom_hook(cls_, hook)
    except ValueError:
        raise ValueError("pass custom_encode_hooks as (class, hook) tuple")


def obj_class_repr(obj):
    return repr(getattr(obj, '__class__', ''))


class FixturesEncoder(JSONEncoder):
    def __init__(self, custom_hooks=None, *args, **kwargs):
        super(FixturesEncoder, self).__init__(*args, **kwargs)
        self._custom_hooks = {}
        add_hooks(self, custom_hooks)

    def default(self, obj):
        obj_clas_repr = obj_class_repr(obj)

        if obj_clas_repr in self._custom_hooks:
            encoder = self._custom_hooks[obj_clas_repr]
            transformed_obj = encoder(obj)
        else:
            try:
                transformed_obj = super(FixturesEncoder, self).default(obj)
            except (TypeError, ValueError):
                if isinstance(obj, datetime):
                    transformed_obj = {
                        DT_TYPE_ATTR: obj.isoformat()
                    }
                else:
                    try:
                        transformed_obj = {CPICKLE_DUMP_ATTR: cPickle.dumps(obj)}
                    except TypeError:
                        transformed_obj = {'repr': repr(obj)}
        if isinstance(transformed_obj, dict):
            transformed_obj[CLASS_TYPE_ATTR] = obj_clas_repr
        return transformed_obj

    def add_custom_hook(self, object_class, hook):
        if isinstance(object_class, object) and inspect.isfunction(hook):
            cls_repr = repr(object_class)
            self._custom_hooks[cls_repr] = hook
        else:
            raise TypeError("custom hook takes two arguments: (class, encoding function for class)")


class FixturesDecoder(JSONDecoder):
    def __init__(self, custom_hooks=None, *args, **kwargs):
        super(FixturesDecoder, self).__init__(object_hook=self.object_hook, *args, **kwargs)
        self._custom_hooks = {}
        add_hooks(self, custom_hooks)

    def object_hook(self, obj):
        if CLASS_TYPE_ATTR not in obj:
            return obj

        type_ = obj.get(CLASS_TYPE_ATTR)
        type_instance = None

        if type_ in self._custom_hooks:
            decoder = self._custom_hooks[type_].get('decoder')
            type_instance = decoder(obj)
        elif type_ == obj_class_repr(datetime):
            dt_string = obj[DT_TYPE_ATTR]
            type_instance = dateutil.parser.parse(dt_string)
        elif type_ and CPICKLE_DUMP_ATTR in obj:
            cpickle_dump = obj.get(CPICKLE_DUMP_ATTR)
            type_instance = cPickle.loads(cpickle_dump.encode('utf8') if isinstance(cpickle_dump, unicode) else cpickle_dump)
        return type_instance

    def add_custom_hook(self, object_class, hook):
        if isinstance(object_class, object) and inspect.isfunction(hook):
            cls_repr = repr(object_class)
            self._custom_hooks[cls_repr] = {
                CLASS_TYPE_ATTR: cls_repr,
                'decoder': hook
            }
        else:
            raise TypeError("custom hook takes two arguments: (class, encoding function for class)")


fixture_serializer = JSONSerializer(encoder=FixturesEncoder(), decoder=FixturesDecoder())
