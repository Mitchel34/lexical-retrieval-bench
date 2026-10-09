"""INVENTED RECEIPT FIXTURES ONLY: these values are not scientific findings."""
import copy
import hashlib
import json
import sys
import tempfile
from pathlib import Path
import unittest
from lexical_retrieval_bench import export
from lexical_retrieval_bench.strict_json import InputError


def invented_fixture():
    # Fabricated converter input, never an actual runner/terminal receipt.
    fixture = dict(export.CONSTANTS)
    fixture.update({k: True for k in export.TRUE_FIELDS})
    fixture.update({k: False for k in export.FALSE_FIELDS})
    fixture.update({k: 1.0 for k in export.SECONDS})
    fixture.update({k: 1024 for k in export.BYTES})
    fixture.update({k: 'a' * 64 for k in ('runner_sha256', 'source_sha256', 'proof_sha256', 'manifest_sha256')})
    fixture.update({'compute_threads': 1, 'monitor_threads': 0, 'supervisor_threads': 1, 'wait4_status': 0,
                    'benchmark_id': 1, 'owned_child_pid': 1, 'lease_id': 'invented-lease',
                    'launch_token': 'invented-token', 'process_identity': {'fixture': 'invented'},
                    'closeout_disk_census_before_receipt': {'fixture': 'invented'}})
    values = dict(export.ACCOUNTING)
    for index, seed in enumerate(export.SEEDS):
        for ranker in export.RANKERS:
            for stratum in export.STRATA:
                for metric in export.METRICS:
                    values['s' + str(seed) + '_' + ranker + '_' + stratum + '_' + metric] = index / 2
    fixture['result'] = {'checks': [{'name': name, 'passed': True} for name in export.CHECKS], 'metrics': values}
    return fixture


def raw_fixture(fixture):
    return json.dumps(fixture, allow_nan=True).encode()


def convert_fixture(fixture):
    raw = raw_fixture(fixture)
    return export.convert(raw, 'a' * 64, hashlib.sha256(raw).hexdigest())


class ExportTests(unittest.TestCase):
    def test_preserve_and_derived_oracle(self):
        fixture = invented_fixture()
        output = convert_fixture(fixture)
        self.assertEqual(output['metrics'], fixture['result']['metrics'])
        self.assertEqual(set(output), {'schema', 'source_sha256', 'metrics', 'resources', 'derived'})
        self.assertEqual(len(output['metrics']), 90)
        self.assertEqual(len(output['derived']), 27)
        for cell in output['derived']:
            self.assertEqual(cell['equal_seed_mean'], 0.5)
            self.assertEqual(cell['sample_standard_deviation'], 0.5)
        self.assertNotIn('invented-lease', json.dumps(output))
        self.assertNotIn('process_identity', output)
        self.assertEqual(output['resources']['charged_cpu_seconds'], 1.0)

    def test_reject_schema_and_terminal_fields(self):
        alterations = [('outcome', 'fail'), ('owned_child_reaped', False), ('wait4_status', True),
                       ('compute_threads', True), ('cpu_seconds', False), ('cpu_seconds', -1),
                       ('peak_memory_bytes', 1.0), ('memory_hard_limit', True),
                       ('cpu_limit_seconds', 0), ('closeout_cpu_margin_seconds', -0.5),
                       ('source_sha256', 'b' * 64), ('runner_sha256', 'A' * 64),
                       ('lease_id', ''), ('process_identity', []), ('unexpected', 1)]
        for key, value in alterations:
            fixture = invented_fixture()
            fixture[key] = value
            with self.subTest(key=key, value=value), self.assertRaises(InputError):
                convert_fixture(fixture)
        fixture = invented_fixture()
        del fixture['lease_id']
        with self.assertRaises(InputError):
            convert_fixture(fixture)

    def test_reject_result_mutations(self):
        for mode in ('missing_metric', 'extra_metric', 'nan', 'bool', 'range', 'count',
                     'missing_check', 'duplicate_check', 'extra_check', 'false_check', 'unknown_check'):
            fixture = invented_fixture()
            values = fixture['result']['metrics']
            checks = fixture['result']['checks']
            key = 's7_overlap_exact_recall5'
            if mode == 'missing_metric': del values[key]
            elif mode == 'extra_metric': values['extra'] = 0
            elif mode == 'nan': values[key] = float('nan')
            elif mode == 'bool': values[key] = True
            elif mode == 'range': values[key] = 1.1
            elif mode == 'count': values['first_pass_rankings'] = 1
            elif mode == 'missing_check': checks.pop()
            elif mode == 'duplicate_check': checks[-1] = copy.deepcopy(checks[0])
            elif mode == 'extra_check': checks.append(copy.deepcopy(checks[0]))
            elif mode == 'false_check': checks[0]['passed'] = False
            else: checks[0]['name'] = 'unknown'
            with self.subTest(mode=mode), self.assertRaises(InputError):
                convert_fixture(fixture)

    def test_digest_and_exclusive_file(self):
        raw = raw_fixture(invented_fixture())
        with self.assertRaises(InputError):
            export.convert(raw, 'a' * 64, '0' * 64)
        with tempfile.TemporaryDirectory() as directory:
            source, output = Path(directory) / 'invented.json', Path(directory) / 'output.json'
            source.write_bytes(raw)
            export.export_file(source, output, 'a' * 64, hashlib.sha256(raw).hexdigest())
            expected = output.read_bytes()
            with self.assertRaises(FileExistsError):
                export.export_file(source, output, 'a' * 64, hashlib.sha256(raw).hexdigest())
            self.assertEqual(output.read_bytes(), expected)

    def test_export_module_has_no_core_import(self):
        # Static source assertion complements review; no evaluator execution.
        import ast
        tree = ast.parse(Path(export.__file__).read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                self.assertNotIn(node.module, ('core', 'lexical_retrieval_bench.core'))


class ExportTransportTests(unittest.TestCase):
    def test_malformed_and_bounded_transport(self):
        fixture = invented_fixture()
        valid = raw_fixture(fixture)
        duplicate = valid[:-1] + b',"kind":"benchmark-receipt"}'
        for raw in (duplicate, b'{' * 17, b' ' * (1024 * 1024 + 1), b'\xff',
                    b'{"x":1e999}', b'{"x":12345678901234567}',
                    b'{"x":"\\ud800"}', valid + b'{}'):
            with self.subTest(prefix=raw[:40]), self.assertRaises(InputError):
                export.convert(raw, 'a' * 64, hashlib.sha256(raw).hexdigest())

    def test_all_resource_and_scope_type_rejections(self):
        for key in export.SECONDS:
            for bad in (True, -1, float('inf'), float('nan'), '1'):
                fixture = invented_fixture()
                fixture[key] = bad
                with self.subTest(key=key, value=bad), self.assertRaises(InputError):
                    convert_fixture(fixture)
        for key in export.BYTES:
            for bad in (True, -1, 1.0):
                fixture = invented_fixture()
                fixture[key] = bad
                with self.subTest(key=key, value=bad), self.assertRaises(InputError):
                    convert_fixture(fixture)
        for key in export.TRUE_FIELDS + export.FALSE_FIELDS:
            fixture = invented_fixture()
            fixture[key] = int(fixture[key])
            with self.subTest(key=key), self.assertRaises(InputError):
                convert_fixture(fixture)
        fixture = invented_fixture()
        fixture['measured_cpu_before_closeout_seconds'] = 2
        with self.assertRaises(InputError):
            convert_fixture(fixture)

    def test_nested_duplicates_and_failed_export_preserves_absence(self):
        raw = raw_fixture(invented_fixture()).replace(b'"passed": true', b'"passed": true, "passed": true', 1)
        with self.assertRaises(InputError):
            export.convert(raw, 'a' * 64, hashlib.sha256(raw).hexdigest())
        with tempfile.TemporaryDirectory() as directory:
            source, output = Path(directory) / 'invented-invalid.json', Path(directory) / 'absent.json'
            source.write_bytes(raw)
            with self.assertRaises(InputError):
                export.export_file(source, output, 'a' * 64, hashlib.sha256(raw).hexdigest())
            self.assertFalse(output.exists())
