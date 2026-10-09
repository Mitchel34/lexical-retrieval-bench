"""Convert an owner-verified receipt. Never import ranking/evaluation code."""
import hashlib
import math
from pathlib import Path
import sys
from .strict_json import InputError, encode, parse

RANKERS = ('overlap', 'tfidf', 'bm25')
STRATA = ('exact', 'noisy', 'mismatch')
METRICS = ('recall5', 'mrr10', 'ndcg10')
SEEDS = (7, 23, 101)
ACCOUNTING = {'seed_count': 3, 'documents_per_seed': 48, 'total_documents': 144,
              'queries_per_seed': 36, 'total_queries': 108, 'ranker_count': 3,
              'first_pass_rankings': 324, 'repeat_rankings': 324, 'total_rankings': 648}
CHECKS = ('dataset_counts', 'unique_ids', 'latent_qrels', 'paired_qrels',
          'generation_repeat', 'ranking_counts', 'ranking_order', 'finite_scores',
          'explanation_sums', 'repeat_equal', 'metric_bounds', 'contract_keys')
ENVELOPE = frozenset('''kind control_mode memory_hard_limit cpu_hard_limit_against_hostile_code
os_network_sandbox hostile_code_safe additional_external_services_used compute_threads monitor_threads
supervisor_threads outcome reason cpu_seconds peak_memory_bytes wall_seconds worker_cpu_seconds
supervisor_cpu_seconds worker_peak_memory_bytes supervisor_peak_memory_bytes memory_measurement
process_tree_stopped result owned_child_pid owned_child_reaped wait4_status descendants_allowed
limits_installation_confirmed memory_limit_bytes cpu_limit_seconds wall_limit_seconds runner_sha256
benchmark_id proof_sha256 source_sha256 lease_id launch_token manifest_sha256 process_identity
cpu_accounting measured_cpu_before_closeout_seconds measured_cpu_is_lower_bound_before_final_receipt_and_db
closeout_cpu_margin_seconds closeout_disk_census_before_receipt'''.split())
CONSTANTS = {'kind': 'benchmark-receipt', 'control_mode': 'trusted-local-python-operational-v1',
             'outcome': 'pass', 'reason': 'passed',
             'cpu_accounting': 'at_least_full_reservation_and_observed_usage_no_refund',
             'memory_measurement': 'sum_of_process_high_water_marks_conservative_not_simultaneous_rss'}
TRUE_FIELDS = ('process_tree_stopped', 'owned_child_reaped', 'limits_installation_confirmed',
               'measured_cpu_is_lower_bound_before_final_receipt_and_db')
FALSE_FIELDS = ('memory_hard_limit', 'cpu_hard_limit_against_hostile_code', 'os_network_sandbox',
                'hostile_code_safe', 'additional_external_services_used', 'descendants_allowed')
SECONDS = ('cpu_seconds', 'wall_seconds', 'worker_cpu_seconds', 'supervisor_cpu_seconds',
           'cpu_limit_seconds', 'wall_limit_seconds', 'measured_cpu_before_closeout_seconds',
           'closeout_cpu_margin_seconds')
BYTES = ('peak_memory_bytes', 'worker_peak_memory_bytes', 'supervisor_peak_memory_bytes', 'memory_limit_bytes')
PUBLIC_RESOURCES = ('measured_cpu_before_closeout_seconds', 'wall_seconds', 'peak_memory_bytes',
                    'worker_peak_memory_bytes', 'supervisor_peak_memory_bytes', 'cpu_accounting',
                    'memory_measurement', 'measured_cpu_is_lower_bound_before_final_receipt_and_db',
                    'memory_hard_limit', 'cpu_hard_limit_against_hostile_code')


def require(ok):
    if not ok:
        raise InputError('invalid_schema')


def digest(value):
    return type(value) is str and len(value) == 64 and all(c in '0123456789abcdef' for c in value)


def finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def convert(raw, source_sha256, receipt_sha256):
    require(digest(source_sha256) and digest(receipt_sha256))
    require(type(raw) is bytes and len(raw) <= 1024 * 1024)
    require(hashlib.sha256(raw).hexdigest() == receipt_sha256)
    receipt = parse(raw, 1024 * 1024, 16)
    require(type(receipt) is dict and set(receipt) == ENVELOPE)
    require(all(type(receipt[k]) is str and receipt[k] == v for k, v in CONSTANTS.items()))
    require(all(receipt[k] is True for k in TRUE_FIELDS))
    require(all(receipt[k] is False for k in FALSE_FIELDS))
    for key, value in (('compute_threads', 1), ('monitor_threads', 0), ('supervisor_threads', 1), ('wait4_status', 0)):
        require(type(receipt[key]) is int and receipt[key] == value)
    for key in ('benchmark_id', 'owned_child_pid'):
        require(type(receipt[key]) is int and receipt[key] > 0)
    for key in ('runner_sha256', 'proof_sha256', 'source_sha256', 'manifest_sha256'):
        require(digest(receipt[key]))
    require(receipt['source_sha256'] == source_sha256)
    require(all(finite(receipt[k]) and receipt[k] >= 0 for k in SECONDS))
    require(all(type(receipt[k]) is int and receipt[k] >= 0 for k in BYTES))
    require(all(receipt[k] > 0 for k in ('memory_limit_bytes', 'cpu_limit_seconds', 'wall_limit_seconds')))
    require(receipt['cpu_seconds'] >= receipt['measured_cpu_before_closeout_seconds'])
    for key in ('lease_id', 'launch_token'):
        require(type(receipt[key]) is str and 1 <= len(receipt[key]) <= 256)
    require(type(receipt['process_identity']) is dict and type(receipt['closeout_disk_census_before_receipt']) is dict)
    result = receipt['result']
    require(type(result) is dict and set(result) == {'checks', 'metrics'})
    checks = result['checks']
    require(type(checks) is list and len(checks) == len(CHECKS))
    names = set()
    for row in checks:
        require(type(row) is dict and set(row) == {'name', 'passed'})
        require(type(row['name']) is str and row['name'] in CHECKS and row['name'] not in names)
        require(row['passed'] is True)
        names.add(row['name'])
    values = result['metrics']
    keys = ['s' + str(s) + '_' + r + '_' + z + '_' + m
            for s in SEEDS for r in RANKERS for z in STRATA for m in METRICS]
    require(type(values) is dict and set(values) == set(keys) | set(ACCOUNTING))
    require(all(finite(values[k]) and -1e-12 <= values[k] <= 1 + 1e-12 for k in keys))
    require(all(finite(values[k]) and values[k] == v for k, v in ACCOUNTING.items()))
    derived = []
    for ranker in RANKERS:
        for stratum in STRATA:
            for metric in METRICS:
                observations = [values['s' + str(s) + '_' + ranker + '_' + stratum + '_' + metric] for s in SEEDS]
                mean = sum(observations) / 3
                deviation = math.sqrt(sum((v - mean) ** 2 for v in observations) / 2)
                derived.append({'ranker': ranker, 'stratum': stratum, 'metric': metric,
                                'equal_seed_mean': mean, 'sample_standard_deviation': deviation})
    resources = {key: receipt[key] for key in PUBLIC_RESOURCES}
    resources['charged_cpu_seconds'] = receipt['cpu_seconds']
    return {'schema': 'lexical-retrieval-results/1', 'source_sha256': source_sha256,
            'metrics': dict(values), 'resources': resources, 'derived': derived}


def export_file(receipt_path, output_path, source_sha256, receipt_sha256):
    with Path(receipt_path).open('rb') as stream:
        raw = stream.read(1024 * 1024 + 1)
    output = encode(convert(raw, source_sha256, receipt_sha256), 256 * 1024)
    with Path(output_path).open('xb') as stream:
        stream.write(output)


def main():
    # Explicit positional contract avoids input-echoing argparse errors.
    if len(sys.argv) != 5:
        sys.stderr.write('usage: python -m lexical_retrieval_bench.export RECEIPT OUTPUT SOURCE_SHA256 RECEIPT_SHA256\n')
        return 2
    try:
        export_file(*sys.argv[1:])
    except (OSError, ValueError, TypeError):
        sys.stderr.write('receipt_export_rejected\n')
        return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
