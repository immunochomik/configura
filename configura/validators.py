

__all__ = [
    'ip4'
]


def ip4(value):
    # noinspection PyBroadException
    try:
        return all([-1 < int(part) < 256 for part in value.split('.')])
    except:  # noqa
        return False
