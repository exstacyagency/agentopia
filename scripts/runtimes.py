from __future__ import annotations

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

    def report(self) -> str:
        lines = ["runtime readiness report:"]
        fields = [
            ("PAPERCLIP", self.paperclip_image, self.paperclip_url, self.paperclip_api_key),
            ("HERMES", self.hermes_image, self.hermes_model_provider, self.hermes_model, self.hermes_api_key),
        ]
        for name, *values in fields:
            lines.append(f"- {name}:")
            labels = ["image", "url/provider", "model", "api key"]
            for label, value in zip(labels, values, strict=False):
                status = "ok" if value else "missing"
                lines.append(f"  - {label}: {status}")
        missing = self.missing()
        if missing:
            lines.append("missing vars:")
            lines.extend(f"- {key}" for key in missing)
        else:
            lines.append("all runtime targets present")
        return "\n".join(lines)

    def ok(self) -> bool:
        return not self.missing()
