from datetime import datetime

from future.utils import string_types

if hasattr(datetime, 'timestamp'):
    # Python 3.3+
    def _timestamp(dt_obj):
        return dt_obj.timestamp()
else:
    # Python < 3.3 (incl 2.7)
    from time import mktime


    def _timestamp(dt_obj):
        return mktime(dt_obj.timetuple())


def to_timestamp(dt_obj):
    """
    Args:
        dt_obj (:class:`datetime.datetime`):

    Returns:
        int:

    """
    if not dt_obj:
        return None

    return int(_timestamp(dt_obj))


def from_timestamp(unixtime):
    """
    Args:
        unixtime (int):

    Returns:
        datetime.datetime:

    """
    if not unixtime:
        return None

    return datetime.fromtimestamp(unixtime // 1e3)


def get_enum(value, enum_class, var_name):
    if value:
        if isinstance(value, enum_class):
            return value

        if isinstance(value, string_types):
            try:
                return enum_class[value]
            except KeyError:
                raise TypeError("{var_name} must be {enum_class} object or str value of {enum_class}".format(enum_class=enum_class.__name__, var_name=var_name))
        else:
            raise TypeError("{var_name} must be {enum_class} object or str value of {enum_class}".format(enum_class=enum_class.__name__, var_name=var_name))
    else:
        return value


def get_hex(value, var_name):
    if value:
        if not value.startswith('#'):
            raise TypeError("{var_name} must be valid hex color value".format(var_name=var_name))
        else:
            for ch in value[1:]:
                if ch not in "1234567890ABCDEFabcdef":
                    raise TypeError("{var_name} must be valid hex color value".format(var_name=var_name))
    return value
