from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RuntimeTargets:
    paperclip_image: str
    hermes_image: str
    paperclip_url: str
    paperclip_api_key: str
    hermes_model_provider: str
    hermes_model: str
    hermes_api_key: str

    @classmethod
    def from_env(cls, env_path: Path | None = None) -> "RuntimeTargets":
        env = {}
        if env_path and env_path.exists():
            for line in env_path.read_text().splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                env[key.strip()] = value.strip()
        data = {
            "paperclip_image": os.environ.get("PAPERCLIP_IMAGE", env.get("PAPERCLIP_IMAGE", "")).strip(),
            "hermes_image": os.environ.get("HERMES_IMAGE", env.get("HERMES_IMAGE", "")).strip(),
            "paperclip_url": os.environ.get("PAPERCLIP_URL", env.get("PAPERCLIP_URL", "")).strip(),
            "paperclip_api_key": os.environ.get("PAPERCLIP_API_KEY", env.get("PAPERCLIP_API_KEY", "")).strip(),
            "hermes_model_provider": os.environ.get("HERMES_MODEL_PROVIDER", env.get("HERMES_MODEL_PROVIDER", "")).strip(),
            "hermes_model": os.environ.get("HERMES_MODEL", env.get("HERMES_MODEL", "")).strip(),
            "hermes_api_key": os.environ.get("HERMES_API_KEY", env.get("HERMES_API_KEY", "")).strip(),
        }
        return cls(**data)

    def missing(self) -> list[str]:
        missing = []
        for key, value in self.__dict__.items():
            if not value:
                missing.append(key.upper())
        return missing

    def report_data(self) -> dict:
        return {
            "paperclip": {
                "image": bool(self.paperclip_image),
                "url": bool(self.paperclip_url),
                "api_key": bool(self.paperclip_api_key),
            },
            "hermes": {
                "image": bool(self.hermes_image),
                "model_provider": bool(self.hermes_model_provider),
                "model": bool(self.hermes_model),
                "api_key": bool(self.hermes_api_key),
            },
            "missing": self.missing(),
            "ok": self.ok(),
        }

    def report(self) -> str:
        data = self.report_data()
        lines = ["runtime readiness report:"]
        for service, values in (("PAPERCLIP", data["paperclip"]), ("HERMES", data["hermes"])):
            lines.append(f"- {service}:")
            for label, ok in values.items():
                status = "ok" if ok else "missing"
                lines.append(f"  - {label}: {status}")
        if data["missing"]:
            lines.append("missing vars:")
            lines.extend(f"- {key}" for key in data["missing"])
        else:
            lines.append("all runtime targets present")
        return "\n".join(lines)

    def report_json(self) -> str:
        return json.dumps(self.report_data(), indent=2) + "\n"

    def dashboard(self) -> str:
        data = self.report_data()
        lines = ["runtime dashboard:"]
        for service_name in ("paperclip", "hermes"):
            service = data[service_name]
            line = f"- {service_name.title():<9} | "
            line += "ready" if all(service.values()) else "not ready"
            lines.append(line)
        lines.append(f"overall    | {'ready' if data['ok'] else 'not ready'}")
        return "\n".join(lines)

    def startup_plan(self) -> dict:
        data = self.report_data()
        return {
            "ready": data["ok"],
            "steps": [
                {
                    "name": "paperclip",
                    "ready": all(data["paperclip"].values()),
                    "missing": [k for k, v in data["paperclip"].items() if not v],
                },
                {
                    "name": "hermes",
                    "ready": all(data["hermes"].values()),
                    "missing": [k for k, v in data["hermes"].items() if not v],
                },
            ],
        }

    def startup_plan_json(self) -> str:
        return json.dumps(self.startup_plan(), indent=2) + "\n"

    def ok(self) -> bool:
        return not self.missing()
