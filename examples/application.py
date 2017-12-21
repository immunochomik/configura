
import os
from tempfile import gettempdir
from textwrap import dedent

from configura import Factory, YamlValuesLoader, ip4

CONFIG_PATH = os.path.join(gettempdir(), 'config-example.yml')


def write_config_file():
    yaml_cfg = dedent("""
        database:
          port: 5432
          host: 10.25.134.1
          user: adam
          pwd: adam!
        webserver:
          port: 
        workers:
          concurrency: 2
        """)
    with open(CONFIG_PATH, 'w') as fd:
        fd.write(yaml_cfg)


class ExampleFactory(Factory):

    _simple_expected_ = {
        'database': {
            'port': [int, 5432],
            'host': [ip4, '0.0.0.0'],
            'user': [str],
            'pwd': [str],
        },
        'webserver': {
            'port': [int, 5001]
        },
        'workers': {
            'concurrency': [int, 1]
        }
    }


if __name__ == '__main__':
    write_config_file()

    config = ExampleFactory(YamlValuesLoader(CONFIG_PATH)).make_config()

    assert config.database.port       == 5432
    assert config.database.host       == '10.25.134.1'
    assert config.database.user       == 'adam'
    assert config.database.pwd        == 'adam!'
    assert config.webserver.port      == 5001
    assert config.workers.concurrency == 2

    os.remove(CONFIG_PATH)

