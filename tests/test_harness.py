import contextlib
import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from harness import grade


class RecordedPlayback:
    """Test double replays saved responses only; cannot answer new inputs."""
    def __init__(self, corrupt=None):
        self.steps = grade.recorded_checks()
        self.index = 0
        self.corrupt = corrupt
        self.closed = False

    def call(self, operation, *args, **kwargs):
        step = self.steps[self.index]
        if json.loads(json.dumps([operation, args, kwargs])) != [step['operation'], step['args'], step['kwargs']]:
            raise ValueError('UNRECORDED_INPUT')
        result = copy.deepcopy(step['expected'])
        if self.index == 0 and self.corrupt == 'status':
            result[0] = 1 - result[0]
        if self.index == 3 and self.corrupt == 'peak':
            result[1][0] += 1
        if self.index == 3 and self.corrupt == 'flag':
            result[2][0] ^= 1
        self.index += 1
        return result

    def load(self, *args, **kwargs):
        return self.call('load', *args, **kwargs)

    def match(self, *args, **kwargs):
        return self.call('match', *args, **kwargs)

    def close(self):
        self.closed = True


class HarnessTests(unittest.TestCase):
    def test_recorded_playback(self):
        result = grade.verify(RecordedPlayback)
        self.assertEqual((result['status'], result['passed_checks']), ('PASS', 343))

    def test_corrupt_recorded_outputs_rejected(self):
        for kind in ['status', 'peak', 'flag']:
            with self.subTest(kind=kind):
                self.assertEqual(grade.verify(lambda: RecordedPlayback(kind))['status'], 'FAIL')

    def test_no_engine_is_not_a_conformance_pass(self):
        stream = io.StringIO()
        with contextlib.redirect_stdout(stream):
            self.assertEqual(grade.main([]), 0)
        result = json.loads(stream.getvalue())
        self.assertEqual(result['harness_status'], 'READY_ENGINE_NOT_TESTED')
        self.assertEqual(result['engine']['status'], 'ENGINE_NOT_SUPPLIED')

    def test_missing_library_error_sanitized(self):
        stream = io.StringIO()
        with contextlib.redirect_stdout(stream):
            self.assertEqual(grade.main(['--engine', '/private-canary/missing.so']), 1)
        self.assertNotIn('private-canary', stream.getvalue())
        self.assertEqual(json.loads(stream.getvalue())['harness_status'], 'FAIL')

    def test_modified_fixtures_fail_before_native_load(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root/'recorded_checks.json').write_text('{}')
            (root/'recorded_checks.sha256').write_text('0'*64)
            with patch.object(grade, 'FIXTURES', root):
                with self.assertRaisesRegex(ValueError, 'HASH_MISMATCH'):
                    grade.recorded_checks()

    def test_unknown_inputs_not_answered(self):
        with self.assertRaisesRegex(ValueError, 'UNRECORDED_INPUT'):
            RecordedPlayback().load([123])

    def test_write_error_sanitized(self):
        with tempfile.TemporaryDirectory() as directory:
            stream = io.StringIO()
            with contextlib.redirect_stdout(stream):
                self.assertEqual(grade.main(['--output', directory]), 1)
            self.assertNotIn(directory, stream.getvalue())
            self.assertEqual(json.loads(stream.getvalue())['error'], 'REPORT_WRITE_FAILED')
