#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import tempfile
import time
import unittest
from pathlib import Path
from urllib import request

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "fixtures"


class HttpIntegrationTests(unittest.TestCase):
    def load_fixture(self, name: str) -> dict:
        return json.loads((FIXTURES / name).read_text())

    def wait_for(self, url: str, timeout: float = 5.0) -> None:
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                with request.urlopen(url, timeout=0.5):
                    return
            except Exception:
                time.sleep(0.1)
        raise AssertionError(f"timed out waiting for {url}")

    def test_live_http_flow(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = str(Path(tmp) / "paperclip.sqlite3")
            env = os.environ.copy()
            env["PYTHONPATH"] = "."
            env["PAPERCLIP_DB_PATH"] = db_path
            env["HERMES_BASE_URL"] = "http://127.0.0.1:3200"
            env["PAPERCLIP_RESULT_URL"] = "http://127.0.0.1:3100/internal/tasks/{task_id}/result"

            paperclip = subprocess.Popen(
                [str(ROOT / ".venv" / "bin" / "python3"), "paperclip/app.py"],
                cwd=ROOT,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            hermes = subprocess.Popen(
                [str(ROOT / ".venv" / "bin" / "python3"), "hermes/app.py"],
                cwd=ROOT,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            try:
                self.wait_for("http://127.0.0.1:3100/health")
                self.wait_for("http://127.0.0.1:3200/health")

                payload = self.load_fixture("task_request_valid.json")
                req = request.Request(
                    "http://127.0.0.1:3100/tasks",
                    data=json.dumps(payload).encode(),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                try:
                    with request.urlopen(req, timeout=5) as response:
                        body = json.loads(response.read().decode())
                except request.HTTPError as exc:
                    error_body = exc.read().decode()
                    raise AssertionError(f"POST /tasks failed: {exc.code} {error_body}") from exc
                self.assertIn(body["state"], {"running", "succeeded", "failed"})

                deadline = time.time() + 5
                task = None
                while time.time() < deadline:
                    with request.urlopen("http://127.0.0.1:3100/tasks/task_123", timeout=5) as response:
                        task = json.loads(response.read().decode())
                    if task["state"] in {"succeeded", "failed"}:
                        break
                    time.sleep(0.1)
                assert task is not None
                self.assertEqual(task["state"], "succeeded")
                self.assertIn("result", task)
            finally:
                paperclip.terminate()
                hermes.terminate()
                try:
                    paperclip.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    paperclip.kill()
                try:
                    hermes.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    hermes.kill()
                paperclip_stdout, paperclip_stderr = paperclip.communicate(timeout=1)
                hermes_stdout, hermes_stderr = hermes.communicate(timeout=1)
                if paperclip_stderr.strip():
                    print("PAPERCLIP STDERR:\n" + paperclip_stderr)
                if hermes_stderr.strip():
                    print("HERMES STDERR:\n" + hermes_stderr)
                if paperclip.returncode not in (0, -15):
                    raise AssertionError(f"paperclip failed\nSTDOUT:\n{paperclip_stdout}\nSTDERR:\n{paperclip_stderr}")
                if hermes.returncode not in (0, -15):
                    raise AssertionError(f"hermes failed\nSTDOUT:\n{hermes_stdout}\nSTDERR:\n{hermes_stderr}")


if __name__ == "__main__":
    unittest.main()
