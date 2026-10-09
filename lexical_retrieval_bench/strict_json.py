"""Bounded strict JSON transport, separate from the pure evaluation module."""
import json
import math


class InputError(ValueError):
    """A stable error code without user input or environment details."""


def pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            raise InputError('invalid_json')
        result[key] = value
    return result


def integer(value):
    if len(value.lstrip('-')) > 16:
        raise InputError('invalid_json')
    return int(value)


def floating(value):
    result = float(value)
    if not math.isfinite(result):
        raise InputError('invalid_json')
    return result


def constant(value):
    raise InputError('invalid_json')


def parse(raw, limit=262144, depth_limit=8):
    if type(raw) is not bytes or len(raw) > limit:
        raise InputError('input_limit')
    try:
        text = raw.decode('utf-8')
    except UnicodeError:
        raise InputError('invalid_utf8') from None
    if text.startswith('\ufeff'):
        raise InputError('invalid_utf8')
    depth, quoted, escaped = 0, False, False
    for char in text:
        if quoted:
            if escaped:
                escaped = False
            elif char == '\\':
                escaped = True
            elif char == '"':
                quoted = False
        elif char == '"':
            quoted = True
        elif char in '[{':
            depth += 1
            if depth > depth_limit:
                raise InputError('depth_limit')
        elif char in ']}':
            depth -= 1
    try:
        value = json.loads(text, object_pairs_hook=pairs, parse_int=integer,
                           parse_float=floating, parse_constant=constant)
    except (ValueError, RecursionError):
        raise InputError('invalid_json') from None
    stack = [value]
    while stack:
        item = stack.pop()
        if type(item) is str:
            if any(0xD800 <= ord(c) <= 0xDFFF for c in item):
                raise InputError('invalid_schema')
        elif type(item) is dict:
            stack.extend(item.keys())
            stack.extend(item.values())
        elif type(item) is list:
            stack.extend(item)
    return value


def encode(value, limit):
    try:
        raw = (json.dumps(value, ensure_ascii=True, allow_nan=False,
                          separators=(',', ':')) + '\n').encode('ascii')
    except (ValueError, TypeError):
        raise InputError('invalid_schema') from None
    if len(raw) > limit:
        raise InputError('output_limit')
    return raw
