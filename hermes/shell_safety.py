from __future__ import annotations

import shlex


class ShellSafetyError(RuntimeError):
    pass


DISALLOWED_TOKENS = {
    ";",
    "&&",
    "||",
    "|",
    ">",
    ">>",
    "<",
    "2>",
    "&",
    "`",
    "$(",
}

DISALLOWED_COMMANDS = {
    "bash",
    "sh",
    "zsh",
    "fish",
    "python",
    "python3",
    "perl",
    "ruby",
    "node",
    "osascript",
    "sudo",
    "env",
    "xargs",
    "find",
}

ALLOWED_COMMANDS = {
    "pwd",
    "ls",
    "cat",
    "echo",
    "git",
    "grep",
    "sed",
    "awk",
    "head",
    "tail",
    "wc",
    "stat",
    "curl",
    "wget",
    "ping",
    "nc",
}


def validate_shell_command(command: str) -> None:
    stripped = command.strip()
    if not stripped:
        raise ShellSafetyError("shell command must not be empty")

    for token in DISALLOWED_TOKENS:
        if token in stripped:
            raise ShellSafetyError(f"shell command uses disallowed shell syntax: {token}")

    try:
        parts = shlex.split(stripped)
    except ValueError as exc:
        raise ShellSafetyError(f"shell command could not be parsed safely: {exc}") from exc

    if not parts:
        raise ShellSafetyError("shell command must not be empty")

    executable = parts[0].split("/")[-1]
    if executable in DISALLOWED_COMMANDS:
        raise ShellSafetyError(f"shell command uses disallowed executable: {executable}")
    if executable not in ALLOWED_COMMANDS:
        raise ShellSafetyError(f"shell command executable is not in the allowlist: {executable}")
