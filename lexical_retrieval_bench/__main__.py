"""Strict stdin/stdout JSON command line interface."""
import sys
from .core import answer
from .strict_json import InputError, encode, parse


def main():
    try:
        if len(sys.argv) != 1:
            raise InputError('invalid_schema')
        request = parse(sys.stdin.buffer.read(262145))
        result = encode(answer(request), 2 * 1024 * 1024)
    except (ValueError, TypeError, KeyError, OverflowError) as error:
        code = str(error) if isinstance(error, InputError) else 'invalid_schema'
        if code not in ('invalid_json', 'invalid_utf8', 'input_limit', 'depth_limit',
                        'invalid_schema', 'output_limit'):
            code = 'invalid_schema'
        sys.stdout.buffer.write(encode({'error': {'code': code}}, 128))
        return 2
    sys.stdout.buffer.write(result)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
