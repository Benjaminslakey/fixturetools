import cPickle
import json
from datetime import datetime
import dateutil.parser


class Serializer(object):
    def serialize(self, *args, **kwargs):
        raise NotImplementedError("Subclass must implement serialize")

    def deserialize(self, *args, **kwargs):
        raise NotImplementedError("Subclass must implement deserialize")

    @property
    def file_ext(self):
        return getattr(self, "_file_ext", "")


class JSONSerializer(Serializer):
    def __init__(self, encoder=json.JSONEncoder, decoder=json.JSONDecoder, indent=2):
        self._file_ext = "json"
        self._encoder = encoder
        self._decoder = decoder
        self._indent = indent

    def serialize(self, obj, output_format=None, **kwargs):
        indent = None if kwargs.get('compact', False) else self._indent
        return json.dumps(obj, cls=self._encoder, indent=indent)

    def deserialize(self, json_string, **kwargs):
        return json.loads(json_string, cls=self._decoder)


class FixturesEncoder(json.JSONEncoder):
    def default(self, obj):
        transformed_obj = None

        try:
            transformed_obj = super(FixturesEncoder, self).default(obj)
        except (TypeError, ValueError):
            if isinstance(obj, datetime):
                transformed_obj = {
                    '__custom_type__': "datetime",
                    'dt_string': obj.isoformat()
                }
            else:
                try:
                    transformed_obj = {
                        '__custom_type__': "%s.%s" % (obj.__module__, obj.__class__.__name__),
                        'cpickle_dump': cPickle.dumps(obj)
                    }
                except TypeError:
                    transformed_obj = repr(obj)
        finally:
            return transformed_obj


class FixturesDecoder(json.JSONDecoder):
    def __init__(self, *args, **kwargs):
        json.JSONDecoder.__init__(self, object_hook=self.object_hook, *args, **kwargs)

    @staticmethod
    def object_hook(obj):
        if '__custom_type__' not in obj:
            return obj

        type_ = obj.pop('__custom_type__')
        type_instance = None

        if type_ == 'datetime':
            dt_string = obj['dt_string']
            type_instance = dateutil.parser.parse(dt_string)
        elif type_ and 'cpickle_dump' in obj:
            cpickle_dump = obj.get('cpickle_dump')
            type_instance = cPickle.loads(cpickle_dump.encode('utf8') if isinstance(cpickle_dump, unicode) else cpickle_dump)
        return type_instance


fixture_serializer = JSONSerializer(encoder=FixturesEncoder, decoder=FixturesDecoder)
