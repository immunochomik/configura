
__all__ = [
    'Factory',
    'ExpectedItem',
    'ReadOnly',
]


# noinspection PyPep8Naming
class empty:
    pass


class ExpectedItem:
    __slots__ = ('default', '_validator')

    def __init__(self, validate, default=None):
        if type(validate) == type:
            self._validator = lambda val: isinstance(val, validate)
        elif callable(validate):
            self._validator = validate
        else:
            raise TypeError('validate has to be a type (int, float) or function')

        if default is not None:
            if not self.validate(default):
                raise TypeError('Default does not pass validation')

        self.default = default

    def validate(self, val):
        return self._validator(val)

    @property
    def required(self):
        return self.default is None

    @classmethod
    def from_tuple(cls, item):
        kwargs = dict(validate=item[0])
        if item[1:2]:
            kwargs['default'] = item[1]
        return cls(**kwargs)


class ReadOnly:
    __flag_attr_writable = '_read_only_config_is_writable'

    def __init__(self, params=None, freeze=False):
        setattr(self, self.__flag_attr_writable, True)
        params = params or dict()
        for key, value in params.items():
            setattr(self, key, value)

        self._done = freeze

    def __setattr__(self, key, value):
        if key != self.__flag_attr_writable and not getattr(self, self.__flag_attr_writable, False):
            raise AttributeError('Attempt to set value on read only object')
        super(ReadOnly, self).__setattr__(key, value)

    def freeze(self):
        delattr(self, self.__flag_attr_writable)
        return self


class FactoryMeta(type):
    # noinspection PyMissingConstructor,PyUnusedLocal
    def __init__(cls, clsname, bases, clsdict):
        def create(expected):
            root = {}
            for key, description in expected.items():
                if isinstance(description, tuple):
                    root[key] = ExpectedItem.from_tuple(description)
                elif isinstance(description, dict):
                    root[key] = create(description)
                else:
                    raise TypeError("Value of expected key '{}' has to be of type dict or ExpectedItem".format(key))
            return root

        setattr(cls, '_expected', create(getattr(cls, '_simple_expected_', {})))


class Factory(metaclass=FactoryMeta):
    # simple expected is to be overwritten with simple tuples and dicts definition it is used by metaclass to produce
    # _expected
    _simple_expected_ = {}
    _expected = {}

    def __init__(self, loader=None):
        self.loader = loader

    def make_config(self):
        return self.loader.load(factory=self, expected=self.expected)

    @property
    def expected(self):
        return self._expected

    def is_required(self, key, expected=None):
        assert isinstance(key, str), 'Key has to be a string'
        expected = expected or self.expected
        value = expected.get(key, empty)
        if value is empty:
            return False
        if isinstance(value, ExpectedItem):
            return value.required
        # noinspection PyUnresolvedReferences
        return any([self.is_required(key, expected=value) for key in value.keys()])
