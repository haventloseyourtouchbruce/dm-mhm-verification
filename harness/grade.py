# SPDX-License-Identifier: Apache-2.0
"""Compare an externally supplied library against a sealed finite fixture set."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from time import perf_counter_ns
from .loader import Library, NativeStatusError
from .words import int64_word, uint32_word

FIXTURES = Path(__file__).resolve().parents[1] / 'fixtures'


def recorded_checks():
    path = FIXTURES / 'recorded_checks.json'
    if path.stat().st_size > 2_000_000:
        raise ValueError('FIXTURE_SIZE_LIMIT')
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != (FIXTURES / 'recorded_checks.sha256').read_text().strip():
        raise ValueError('FIXTURE_HASH_MISMATCH')
    data = json.loads(raw)
    if data.get('schema_version') != 1 or len(data.get('steps', [])) != 343:
        raise ValueError('FIXTURE_FORMAT')
    for step in data['steps']:
        op, args, kwargs = step['operation'], step['args'], step['kwargs']
        if op not in ('load', 'match') or not isinstance(args, list) or not args:
            raise ValueError('FIXTURE_OPERATION')
        words = args[0]
        if not isinstance(words, list) or len(words) > (4097 if op == 'load' else 128):
            raise ValueError('FIXTURE_COUNT_LIMIT')
        for word in words:
            int64_word(word)
        if op == 'load':
            if len(args) != 1 or kwargs or type(step['expected']) is not int:
                raise ValueError('FIXTURE_LOAD_FORMAT')
        else:
            if len(args) > 3 or set(kwargs) - {'flags'}:
                raise ValueError('FIXTURE_MATCH_FORMAT')
            h = uint32_word(args[1] if len(args) > 1 else 32)
            int64_word(args[2] if len(args) > 2 else 2 * (1 << 32))
            if h > 33 or ('flags' in kwargs and type(kwargs['flags']) is not bool):
                raise ValueError('FIXTURE_ARGUMENT_LIMIT')
            expected = step['expected']
            if not isinstance(expected, list) or len(expected) != 3:
                raise ValueError('FIXTURE_RESULT_FORMAT')
            if len(expected[1]) != len(words) * max(1, min(h, 32)):
                raise ValueError('FIXTURE_OUTPUT_SIZE')
            for word in expected[1]:
                int64_word(word)
            if kwargs.get('flags', True):
                if not isinstance(expected[2], list) or len(expected[2]) != len(words):
                    raise ValueError('FIXTURE_FLAG_SIZE')
                if any(type(v) is not int or not 0 <= v <= 255 for v in expected[2]):
                    raise ValueError('FIXTURE_FLAG_VALUE')
            elif expected[2] is not None:
                raise ValueError('FIXTURE_FLAG_FORMAT')
            if type(expected[0]) is not int or not 0 <= expected[0] <= 6:
                raise ValueError('FIXTURE_STATUS')
    return data['steps']


def verify(factory):
    steps = recorded_checks()
    actual = factory()
    failures = []
    completed = 0
    elapsed_ns = 0
    try:
        for index, step in enumerate(steps):
            start = perf_counter_ns()
            got = getattr(actual, step['operation'])(*step['args'], **step['kwargs'])
            elapsed_ns += perf_counter_ns() - start
            got = json.loads(json.dumps(got))
            completed += 1
            if got != step['expected']:
                failures.append(index)
    finally:
        actual.close()
    return {'status': 'PASS' if not failures else 'FAIL', 'checks': completed,
            'passed_checks': completed - len(failures), 'failed_step_indices': failures,
            'host_replay_call_time_us': elapsed_ns / 1000,
            'timing_boundary': 'sum of mixed fixture calls including Python binding; not the historical benchmark',
            'pass_rule': 'ALL_RECORDED_FIELDS_EXACT'}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--engine', help='Separately supplied authorized native library')
    parser.add_argument('--output')
    parser.add_argument('--worker', action='store_true', help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    report = {'schema_version': 2, 'fixtures': {'status': 'ERROR'},
              'engine': {'status': 'ENGINE_NOT_SUPPLIED'}, 'harness_status': 'FAIL'}
    code = 1
    try:
        steps = recorded_checks()
        report['fixtures'] = {'status': 'HASH_AND_FORMAT_VERIFIED', 'recorded_operations': len(steps)}
        if args.engine is None:
            report['harness_status'] = 'READY_ENGINE_NOT_TESTED'
            code = 0
        elif args.worker:
            report['engine'] = verify(Library(args.engine).context)
            report['harness_status'] = report['engine']['status']
            code = 0 if report['harness_status'] == 'PASS' else 1
        else:
            result = subprocess.run([sys.executable, '-m', 'harness.grade', '--worker', '--engine', args.engine],
                                    capture_output=True, text=True, timeout=180)
            if result.returncode not in (0, 1):
                report['engine'] = {'status': 'ERROR', 'error': 'NATIVE_PROCESS_FAILED'}
            else:
                report = json.loads(result.stdout)
                code = 0 if result.returncode == 0 and report['harness_status'] == 'PASS' else 1
    except Exception as exc:
        report['engine'] = {'status': 'ERROR', 'error': type(exc).__name__}
        if isinstance(exc, NativeStatusError):
            report['engine']['native_status'] = exc.status
    encoded = json.dumps(report, indent=2, sort_keys=True) + '\n'
    if args.output:
        try:
            path = Path(args.output)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(encoded, encoding='utf-8')
        except OSError:
            print(json.dumps({'harness_status': 'FAIL', 'error': 'REPORT_WRITE_FAILED'}))
            return 1
    print(encoded, end='')
    return code


if __name__ == '__main__':
    raise SystemExit(main())
