"""Strict transport and tiny CLI subprocess checks, no evaluation workload."""
import copy
import json
import subprocess
import sys
import unittest
from lexical_retrieval_bench.demo import REQUEST
from lexical_retrieval_bench.strict_json import InputError, encode, parse


class TransportTests(unittest.TestCase):
    def test_transport_rejections(self):
        cases = [(b'\xff', 'invalid_utf8'), (b'\xef\xbb\xbf{}', 'invalid_utf8'),
                 (b'{' * 9, 'depth_limit'), (b' ' * 262145, 'input_limit'),
                 (b'{"a":1,"a":2}', 'invalid_json'), (b'{} {}', 'invalid_json'),
                 (b'NaN', 'invalid_json'), (b'Infinity', 'invalid_json'),
                 (b'-Infinity', 'invalid_json'), (b'1e999', 'invalid_json'),
                 (b'12345678901234567', 'invalid_json'), (b'"\\ud800"', 'invalid_schema'),
                 (b'{"\\udfff":0}', 'invalid_schema'), (b'{"a":', 'invalid_json')]
        for raw, code in cases:
            with self.subTest(raw=raw[:30]), self.assertRaisesRegex(InputError, '^' + code + '$'):
                parse(raw)

    def test_strings_depth_and_output_bound(self):
        self.assertEqual(parse(b'{"x":"{[\\\"}]"}'), {'x': '{["}]'})
        self.assertEqual(parse(b'[' * 8 + b'0' + b']' * 8), [[[[[[[[0]]]]]]]])
        with self.assertRaisesRegex(InputError, 'output_limit'):
            encode({'a': 'b'}, 2)

    def run_cli(self, raw):
        return subprocess.run([sys.executable, '-m', 'lexical_retrieval_bench'], input=raw,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5, check=False)

    def test_real_cli_and_error_contract(self):
        run = self.run_cli(json.dumps(REQUEST).encode())
        self.assertEqual(run.returncode, 0)
        result = json.loads(run.stdout)
        self.assertEqual(set(result), {'version', 'ranker', 'results'})
        self.assertEqual(result['results'][0]['ranking'][0]['document_id'], 'a')
        self.assertEqual(result['results'][0]['ranking'][0]['score'], 1)
        self.assertEqual(run.stderr, b'')
        for raw, code in [(b'NaN', 'invalid_json'), (b'\xff', 'invalid_utf8'),
                          (b'{' * 9, 'depth_limit'), (b' ' * 262145, 'input_limit')]:
            run = self.run_cli(raw)
            self.assertEqual(run.returncode, 2)
            self.assertEqual(json.loads(run.stdout), {'error': {'code': code}})
            self.assertEqual(run.stderr, b'')
            self.assertLess(len(run.stdout), 128)

    def test_schema_cli_errors(self):
        for field, value in [('version', True), ('k', 1.0), ('k', None), ('ranker', []),
                             ('documents', []), ('queries', []), ('qrels', [])]:
            request = copy.deepcopy(REQUEST)
            request[field] = value
            run = self.run_cli(json.dumps(request).encode())
            self.assertEqual(run.returncode, 2)
            self.assertEqual(json.loads(run.stdout), {'error': {'code': 'invalid_schema'}})
            self.assertEqual(run.stderr, b'')

    def test_nested_duplicate_and_schema_failures_through_cli(self):
        valid = json.dumps(REQUEST).encode()
        invalid = [valid.replace(b'"version": 1', b'"version": 1, "version": 1'),
                   valid.replace(b'"id": "a"', b'"id": "a", "id": "a"')]
        for raw in invalid:
            run = self.run_cli(raw)
            self.assertEqual(run.returncode, 2)
            self.assertEqual(json.loads(run.stdout), {'error': {'code': 'invalid_json'}})
            self.assertEqual(run.stderr, b'')
        for kind in ('duplicate_document', 'unknown_query', 'unknown_grade_doc', 'surrogate', 'unknown_field'):
            request = copy.deepcopy(REQUEST)
            if kind == 'duplicate_document': request['documents'].append(request['documents'][0])
            elif kind == 'unknown_query': request['qrels'][0]['query_id'] = 'unknown'
            elif kind == 'unknown_grade_doc': request['qrels'][0]['grades'][0]['document_id'] = 'unknown'
            elif kind == 'surrogate': request['queries'][0]['text'] = '\ud800'
            else: request['qrels'][0]['unknown'] = 1
            run = self.run_cli(json.dumps(request).encode())
            self.assertEqual(run.returncode, 2)
            self.assertEqual(json.loads(run.stdout), {'error': {'code': 'invalid_schema'}})
            self.assertEqual(run.stderr, b'')

    def test_bom_overflow_and_long_integer_cli(self):
        for raw, code in [(b'\xef\xbb\xbf{}', 'invalid_utf8'),
                          (b'{"version":1e999}', 'invalid_json'),
                          (b'{"version":12345678901234567}', 'invalid_json')]:
            run = self.run_cli(raw)
            self.assertEqual(run.returncode, 2)
            self.assertEqual(json.loads(run.stdout), {'error': {'code': code}})
            self.assertEqual(run.stderr, b'')
