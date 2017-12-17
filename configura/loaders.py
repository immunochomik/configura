
import os
from abc import abstractmethod

import yaml

from configura.configura import ConfigItemRequiredException, ConfigItemValidationException
from configura.configura.factory import ReadOnly


class ValuesLoader(object):
    def __init__(self, source):
        self.source = self.parse_source(source)

    @abstractmethod
    def parse_source(self, source):
        pass

    def load(self, factory, expected, source=None):
        root = ReadOnly()
        source = source or self.source

        for key, expected_item in expected.items():
            value = source.get(key, None)
            if value is None:
                if factory.is_required(key):
                    raise ConfigItemRequiredException(key)
                if not isinstance(expected_item, dict):
                    value = expected_item.default

            if isinstance(expected_item, dict):
                setattr(root, key, self.load(factory=factory, expected=expected_item, source=value))
                continue

            if not expected_item.validate(value):
                raise ConfigItemValidationException(key)

            setattr(root, key, value)
        return root.freeze()


class DictValuesLoader(ValuesLoader):
    def parse_source(self, data):
        assert isinstance(data, dict)
        return data


class YamlValuesLoader(ValuesLoader):
    def parse_source(self, source):
        assert os.path.exists(source)
        with open(source, 'r') as fp:
            return yaml.load(fp)
