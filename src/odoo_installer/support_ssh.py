from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import subprocess


SAFE_FILENAME_RE = re.compile(r"[^A-Za-z0-9_.-]+")


@dataclass(frozen=True, slots=True)
class GeneratedSupportKey:
    private_key_path: Path
    public_key_path: Path
    private_key: str
    public_key: str


def _safe_filename(value: str) -> str:
    cleaned = SAFE_FILENAME_RE.sub("_", value.strip()).strip("._-")
    return cleaned or "server"


def default_key_path(host: str, user: str, base_dir: Path | None = None) -> Path:
    root = base_dir or Path.home() / ".odoo-installer" / "support-keys"
    return root / f"{_safe_filename(host)}_{_safe_filename(user)}_rsa.pem"


def generate_support_key(host: str, user: str, *, base_dir: Path | None = None, overwrite: bool = False) -> GeneratedSupportKey:
    """Generate or reuse an RSA key pair in PEM format for the AHD support account.

    The private key stays on the installer's local machine. Only the public key
    is written to the customer's server as authorized_keys content.
    """

    private_key_path = default_key_path(host, user, base_dir=base_dir)
    public_key_path = private_key_path.with_suffix(private_key_path.suffix + ".pub")
    private_key_path.parent.mkdir(parents=True, exist_ok=True)

    if overwrite:
        private_key_path.unlink(missing_ok=True)
        public_key_path.unlink(missing_ok=True)

    if not private_key_path.exists() or not public_key_path.exists():
        subprocess.run(
            [
                "ssh-keygen",
                "-t",
                "rsa",
                "-b",
                "4096",
                "-m",
                "PEM",
                "-f",
                str(private_key_path),
                "-N",
                "",
                "-C",
                f"{user}@{host}",
            ],
            check=True,
            capture_output=True,
            text=True,
        )

    private_key_path.chmod(0o600)
    public_key_path.chmod(0o644)
    return GeneratedSupportKey(
        private_key_path=private_key_path,
        public_key_path=public_key_path,
        private_key=private_key_path.read_text(encoding="utf-8"),
        public_key=public_key_path.read_text(encoding="utf-8").strip(),
    )
