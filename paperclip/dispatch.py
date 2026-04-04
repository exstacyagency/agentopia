from __future__ import annotations

from hermes.executor import HermesExecutor


class HermesDispatchClient:
    def __init__(self, executor: HermesExecutor):
        self.executor = executor

    def submit(self, payload: dict) -> dict:
        return self.executor.execute(payload)
