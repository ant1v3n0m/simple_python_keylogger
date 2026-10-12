import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from recorder import Recorder


class FakeListener:
    def __init__(self, on_press):
        self.on_press = on_press
        self.running = False
        self.joined = False

    def start(self):
        self.running = True

    def stop(self):
        self.running = False

    def join(self, timeout=None):
        self.joined = True

    def press(self, char):
        self.on_press(SimpleNamespace(char=char))


class ListenerFactory:
    def __init__(self):
        self.instances = []

    def __call__(self, on_press):
        listener = FakeListener(on_press)
        self.instances.append(listener)
        return listener


def read_records(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


class RecorderTests(unittest.TestCase):
    def test_start_press_stop_writes_complete_session(self):
        with tempfile.TemporaryDirectory() as directory:
            factory = ListenerFactory()
            recorder = Recorder(listener_factory=factory)
            path = recorder.start(Path(directory), 300)
            factory.instances[-1].press("é")
            recorder.stop()

            records = read_records(path)
            self.assertEqual([record["event"] for record in records], ["start", "key", "stop"])
            self.assertEqual(records[1]["value"], "é")
            self.assertEqual(records[-1]["reason"], "user_stopped")
            self.assertEqual(recorder.count, 1)
            self.assertTrue(factory.instances[-1].joined)

    def test_session_stops_at_configured_limit(self):
        with tempfile.TemporaryDirectory() as directory:
            now = [100.0]
            recorder = Recorder(listener_factory=ListenerFactory(), clock=lambda: now[0])
            path = recorder.start(Path(directory), 60)
            now[0] = 161.0
            recorder.poll()
            self.assertFalse(recorder.running)
            self.assertEqual(read_records(path)[-1]["reason"], "time_limit")

    def test_escape_stops_session_and_is_logged(self):
        with tempfile.TemporaryDirectory() as directory:
            factory = ListenerFactory()
            recorder = Recorder(listener_factory=factory)
            path = recorder.start(Path(directory), 300)
            factory.instances[-1].on_press(SimpleNamespace(name="esc"))
            recorder.poll()

            records = read_records(path)
            self.assertFalse(recorder.running)
            self.assertEqual(records[-2]["value"], "esc")
            self.assertEqual(records[-1]["reason"], "escape_key")

    def test_old_listener_cannot_write_to_new_session(self):
        with tempfile.TemporaryDirectory() as directory:
            factory = ListenerFactory()
            recorder = Recorder(listener_factory=factory)
            recorder.start(Path(directory), 300)
            old_listener = factory.instances[-1]
            recorder.stop()
            new_path = recorder.start(Path(directory), 300)
            old_listener.press("x")
            factory.instances[-1].press("y")
            recorder.stop()

            keys = [record["value"] for record in read_records(new_path) if record["event"] == "key"]
            self.assertEqual(keys, ["y"])

    def test_queue_overflow_stops_instead_of_silently_dropping_events(self):
        with tempfile.TemporaryDirectory() as directory:
            factory = ListenerFactory()
            recorder = Recorder(listener_factory=factory, queue_capacity=1)
            path = recorder.start(Path(directory), 300)
            factory.instances[-1].press("a")
            factory.instances[-1].press("b")
            recorder.poll()

            self.assertFalse(recorder.running)
            self.assertEqual(recorder.stop_reason, "queue_overflow")
            self.assertIn("buffer filled", recorder.last_error)
            self.assertEqual(read_records(path)[-1]["reason"], "queue_overflow")

    def test_write_error_stops_listener_and_closes_file(self):
        class FailingWriter:
            def __init__(self, path):
                self.reason = None

            def write_key(self, timestamp, key):
                raise OSError("disk full")

            def close(self, reason):
                self.reason = reason

        with tempfile.TemporaryDirectory() as directory:
            factory = ListenerFactory()
            writers = []

            def writer_factory(path):
                writer = FailingWriter(path)
                writers.append(writer)
                return writer

            recorder = Recorder(listener_factory=factory, writer_factory=writer_factory)
            recorder.start(Path(directory), 300)
            factory.instances[-1].press("a")
            recorder.poll()

            self.assertFalse(recorder.running)
            self.assertEqual(recorder.stop_reason, "write_error")
            self.assertEqual(writers[-1].reason, "write_error")
            self.assertTrue(factory.instances[-1].joined)
            self.assertIn("disk full", recorder.last_error)

    def test_listener_start_failure_finishes_session(self):
        class BrokenListener(FakeListener):
            def start(self):
                raise RuntimeError("hook unavailable")

        with tempfile.TemporaryDirectory() as directory:
            recorder = Recorder(listener_factory=BrokenListener)
            with self.assertRaisesRegex(RuntimeError, "hook unavailable"):
                recorder.start(Path(directory), 300)
            self.assertFalse(recorder.running)
            paths = list(Path(directory).glob("*.jsonl"))
            self.assertEqual(len(paths), 1)
            self.assertEqual(read_records(paths[0])[-1]["reason"], "listener_error")

    def test_listener_stopping_unexpectedly_ends_session(self):
        with tempfile.TemporaryDirectory() as directory:
            factory = ListenerFactory()
            recorder = Recorder(listener_factory=factory)
            path = recorder.start(Path(directory), 300)
            factory.instances[-1].running = False
            recorder.poll()
            self.assertFalse(recorder.running)
            self.assertEqual(read_records(path)[-1]["reason"], "listener_stopped")

    def test_callback_error_is_reported_and_stops_session(self):
        class BrokenKey:
            @property
            def char(self):
                raise RuntimeError("bad key event")

        with tempfile.TemporaryDirectory() as directory:
            factory = ListenerFactory()
            recorder = Recorder(listener_factory=factory)
            path = recorder.start(Path(directory), 300)
            factory.instances[-1].on_press(BrokenKey())
            recorder.poll()
            self.assertFalse(recorder.running)
            self.assertEqual(read_records(path)[-1]["reason"], "callback_error")
            self.assertIn("bad key event", recorder.last_error)

    def test_duration_is_bounded(self):
        with tempfile.TemporaryDirectory() as directory:
            recorder = Recorder(listener_factory=ListenerFactory())
            with self.assertRaises(ValueError):
                recorder.start(Path(directory), 0)
            with self.assertRaises(ValueError):
                recorder.start(Path(directory), 3601)


if __name__ == "__main__":
    unittest.main()
