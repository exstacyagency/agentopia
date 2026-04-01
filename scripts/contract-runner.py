#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

from contract_runner import ContractRunner


def main() -> None:
    ContractRunner(Path(__file__).resolve().parent.parent).run()
    print("contract runner ok")


if __name__ == "__main__":
    main()
