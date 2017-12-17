

__all__ = [
    'ConfigItemRequiredException',
    'ConfigItemValidationException'
]


class ConfigItemRequiredException(Exception):
    def __init__(self, key):
        super(ConfigItemRequiredException, self).__init__("Config item '{}' is required".format(key))


class ConfigItemValidationException(Exception):
    def __init__(self, key):
        super(ConfigItemValidationException, self).__init__("Config value for item '{}' is not valid".format(key))
