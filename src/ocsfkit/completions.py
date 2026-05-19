from __future__ import annotations

SUPPORTED_SHELLS = {"bash", "zsh", "fish"}


def completion_script(shell: str, command_name: str = "ocsfkit") -> str:
    if shell not in SUPPORTED_SHELLS:
        supported = ", ".join(sorted(SUPPORTED_SHELLS))
        raise ValueError(f"Unsupported shell {shell!r}. Supported shells: {supported}")
    env_name = f"_{command_name.upper()}_COMPLETE"
    if shell == "bash":
        return f'eval "$({env_name}=bash_source {command_name})"\n'
    if shell == "zsh":
        return f'eval "$({env_name}=zsh_source {command_name})"\n'
    return f"{env_name}=fish_source {command_name} | source\n"
