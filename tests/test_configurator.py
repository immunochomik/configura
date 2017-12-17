import os
import tempfile
import uuid
from unittest import TestCase

import yaml

from configura import Factory, ExpectedItem, DictValuesLoader, \
    ConfigItemValidationException, ConfigItemRequiredException, YamlValuesLoader, ip4


class ExpectedItemTestCase(TestCase):
    def test_init_with_type_validator_check_valid(self):
        item = ExpectedItem(validate=int)
        self.assertTrue(item.validate(1))
        self.assertTrue(item.validate(100))
        self.assertTrue(item.validate(111))
        self.assertFalse(item.validate('111'))
        self.assertFalse(item.validate(object))

    def test_init_with_function_validator_check_valid(self):
        def validate(val):
            if isinstance(val, str):
                return 'Oko' in val
            return False

        item = ExpectedItem(validate=validate)
        self.assertFalse(item.validate('bar'))
        self.assertFalse(item.validate('Omko'))
        self.assertFalse(item.validate('Omko'))
        self.assertTrue(item.validate('Oko'))
        self.assertTrue(item.validate('one in five Oko'))

    def test_default_applied(self):
        item = ExpectedItem(validate=int, default=1)
        self.assertEqual(1, item.default)

    def test_required_applied(self):
        item = ExpectedItem(validate=int, required=True)
        self.assertTrue(item.required)

    def test_required_v_default_applied(self):
        with self.assertRaises(TypeError):
            ExpectedItem(validate=int, default=1, required=1)

    def test_default_validation_check_rises(self):
        with self.assertRaises(TypeError):
            ExpectedItem(validate=int, default='ada')

        with self.assertRaises(TypeError):
            ExpectedItem(validate=str, default=1)

        with self.assertRaises(TypeError):
            ExpectedItem.from_tuple((int, False, 'abd'))

        item = ExpectedItem.from_tuple((str, False, 'abd'))
        self.assertEqual('abd', item.default)
        self.assertFalse(item.required)


class ConfiguratorTestCase(TestCase):
    def make_cfg(self, values, expected):
        class FooFactory(Factory):
            _simple_expected_ = expected

        return FooFactory(loader=DictValuesLoader(source=values)).make_config()

    def test_validate_expected_wrong_types_check_rises(self):
        with self.assertRaises(ConfigItemValidationException) as cont:
            cfg = self.make_cfg(
                values={
                    'one': 5,
                    'nest1': {
                        'two': {'three', 1},
                    },
                },
                expected={
                    'one': (int, True),
                    'not': (int, False, 1),
                    'nest1': {
                        'two': (float, False, 1.5),
                    }})
        self.assertEqual(str(cont.exception), "Config value for item 'two' is not valid")

        with self.assertRaises(ConfigItemValidationException) as cont:
            cfg = self.make_cfg(
                values={'one': [1, 2, 3]},
                expected={'one': (int, True)})
        self.assertEqual(str(cont.exception), "Config value for item 'one' is not valid")

    def test_load_valid_check_values(self):
        cfg = self.make_cfg(
            values={
                'one': 5,
                'nest1': {
                    'three': 1.5,
                    'nest2': {
                        'nest3': {
                            'five': 'this is string'
                        }
                    }
                },
            },
            expected={
                'one': (int, True),
                'not': (int, False, 1),
                'nest1': {
                    'two': (float, False, 1.5),
                    'three': (float, False),
                    'nest2': {
                        'nest3': {
                            'five': (str, True)
                        }
                    }
                }})
        self.assertEqual(cfg.one, 5)
        self.assertEqual(cfg.nest1.two, 1.5)
        self.assertEqual(cfg.nest1.three, 1.5)
        self.assertEqual(cfg.nest1.nest2.nest3.five, 'this is string')
        with self.assertRaises(AttributeError):
            cfg.one = 1
        with self.assertRaises(AttributeError):
            cfg.nest1.nest2.nest3.bar = 1

    def test_default_and_in_source_check_source_used(self):
        cfg = self.make_cfg(
            values={
                'one': 1,
                'nest': {
                    'def2': '10.254.10.170'
                }
            },
            expected={
                'one': (int, False, 4),
                'nest': {
                    'def2': (ip4, False, '0.0.0.0')
                }

            })
        self.assertEqual(cfg.one, 1)
        self.assertEqual(cfg.nest.def2, '10.254.10.170')

    def test_default_not_in_source_check_default_used(self):
        cfg = self.make_cfg(
            values={},
            expected={
                'one': (int, False, 4),
                'nest': {
                    'def2': (ip4, False, '0.0.0.0')
                }

            })
        self.assertEqual(cfg.one, 4)
        self.assertEqual(cfg.nest.def2, '0.0.0.0')

    def test_required_not_in_source_raises(self):
        with self.assertRaises(ConfigItemRequiredException) as cont:
            cfg = self.make_cfg(
                values={},
                expected={
                    'one': (int, False, 4),
                    'nest': {
                        'def2': (ip4, True)
                    }

                })
        self.assertEqual(str(cont.exception), "Config item 'nest' is required")

    def test_required_in_source_check_value(self):
        cfg = self.make_cfg(
            values={
                'one': 1,
                'nest': {
                    'def2': '10.254.10.170'
                }
            },
            expected={
                'one': (int, False, 4),
                'nest': {
                    'def2': (ip4, True)
                }

            })
        self.assertEqual(cfg.one, 1)
        self.assertEqual(cfg.nest.def2, '10.254.10.170')

    def test_source_contains_unknown_items_check_ignored(self):
        cfg = self.make_cfg(
            values={
                'one': 1,
                'nest': {
                    'def2': '10.254.10.170'
                },
                'web': {
                    'port': 1234
                }
            },
            expected={
                'one': (int, False, 4),
                'nest': {
                    'def2': (ip4, True)
                }

            })
        self.assertEqual(cfg.one, 1)
        self.assertEqual(cfg.nest.def2, '10.254.10.170')
        with self.assertRaises(AttributeError):
            _ = cfg.web.port

    def test_setting_item_on_loaded_config_check_rises(self):
        cfg = self.make_cfg(
            values={},
            expected={
                'one': (int, False, 4),
                'nest': {
                    'def2': (ip4, False, '0.0.0.0')
                }

            })
        self.assertEqual(cfg.one, 4)
        self.assertEqual(cfg.nest.def2, '0.0.0.0')
        with self.assertRaises(AttributeError):
            cfg.web.port = 1234

        with self.assertRaises(AttributeError):
            cfg.one = 1234

    def test_validate_function_check_raises(self):
        with self.assertRaises(ConfigItemValidationException) as cont:
            cfg = self.make_cfg(
                values={
                    'nest': {
                        'def2': '256.254.10.170'
                    }
                },
                expected={
                    'nest': {
                        'def2': (ip4, False, '0.0.0.0')
                    }

                })
        self.assertEqual(str(cont.exception), "Config value for item 'def2' is not valid")


class YamlValuesConfigTestCase(TestCase):
    data = {
        'one': 1,
        'nest': {
            'def2': '10.254.10.170'
        },
        'web': {
            'port': 1234
        },
        'ania': 'ma kota',
        'foo': {
            'bar': 1
        }
    }

    def setUp(self):
        self.path = os.path.join(tempfile.gettempdir(), 'test_config_{}'.format(uuid.uuid4()))
        with open(self.path, 'w') as fd:
            yaml.dump(self.data, fd, default_flow_style=False)

    def tearDown(self):
        if os.path.exists(self.path):
            os.remove(self.path)

    def make_cfg(self, expected):
        class FooFactory(Factory):
            _simple_expected_ = expected

        return FooFactory(YamlValuesLoader(self.path)).make_config()

    def test_load_valid_check_values(self):
        cfg = self.make_cfg({
            'one': (int, True),
            'nest': {
                'def2': (ip4, False, '0.0.0.0')
            },
            'web': {
                'port': (int, True)
            }
        })
        self.assertEqual(cfg.one, 1)
        self.assertEqual(cfg.nest.def2, '10.254.10.170')
        self.assertEqual(cfg.web.port, 1234)

    def test_load_valid_check_defaults(self):
        cfg = self.make_cfg({
            'one': (int, True),
            'nest': {
                'def2': (ip4, False, '0.0.0.0')
            },
            'web': {
                'port': (int, True)
            },
            'database': {
                'port': (int, False, 5432),
                'pwd': (str, False, 'foo'),
                'user': (str, False, 'amp')
            }
        })
        self.assertEqual(cfg.one, 1)
        self.assertEqual(cfg.nest.def2, '10.254.10.170')
        self.assertEqual(cfg.web.port, 1234)
        self.assertEqual(cfg.database.port, 5432)
        self.assertEqual(cfg.database.user, 'amp')
        self.assertEqual(cfg.database.pwd, 'foo')

    def test_file_does_not_exist_check_fail(self):
        os.remove(self.path)
        with self.assertRaises(AssertionError):
            _ = self.make_cfg({
                'one': (int, True),
                'nest': {
                    'def2': (ip4, False, '0.0.0.0')
                },
                'web': {
                    'port': (int, True)
                }
            })

    def test_file_contains_unknown_items_check_ignored(self):
        cfg = self.make_cfg({
            'one': (int, True),
            'nest': {
                'def2': (ip4, False, '0.0.0.0')
            },
            'web': {
                'port': (int, True)
            }
        })
        self.assertEqual(cfg.one, 1)
        self.assertEqual(cfg.nest.def2, '10.254.10.170')
        self.assertEqual(cfg.web.port, 1234)
        with self.assertRaises(AttributeError):
           _ = cfg.ania

        with self.assertRaises(AttributeError):
           _ = cfg.foo.bar


class ConfiguratorIsRequiredTestCase(TestCase):
    def setUp(self):
        class DummyFactory(Factory):
            _simple_expected_ = {
                'one': (int, True),
                'not': (int, False, 1),
                'nest1': {
                    'two': (float, False, 1.5),
                    'three': (float, False),
                    'nest2': {
                        'four': (int, False),
                        'nest3': {
                            'five': (str, True)
                        }
                    }
                },

                'nest_not_required': {
                    'two': (float, False),
                    'three': (float, False),
                    'nest2': {
                        'four': (int, False),
                        'nest3': {
                            'five': (str, False)
                        }
                    }
                }
            }

        self.cfg = DummyFactory()

    def test_is_required_simple_check_true(self):
        self.assertTrue(self.cfg.is_required('one'))
        self.assertFalse(self.cfg.is_required('not'))
        self.assertFalse(self.cfg.is_required('notIn'))

    def test_is_required_nested_check_true(self):
        self.assertTrue(self.cfg.is_required('nest1'))

    def test_is_required_nested_check_false(self):
        self.assertFalse(self.cfg.is_required('nest_not_required'))


class IsIP4TestCase(TestCase):
    def test_valid_values_check_true(self):
        values = ['0.0.0.0', '127.0.0.1', '254.0.254.245']
        for one in values:
            self.assertTrue(ip4(one))

    def test_invalid_values_check_false(self):
        values = ['L.0.0.0', '', '.0.254.245', '....', '256.1.1.1', 'a.b.c.d', '-2.1.1.1']
        for one in values:
            self.assertFalse(ip4(one))
