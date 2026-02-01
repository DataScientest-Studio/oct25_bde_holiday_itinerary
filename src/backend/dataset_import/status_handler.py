import json
from pathlib import Path
from typing import Any, Dict


class ProcessRunning(RuntimeError):
    def __init__(self, process: str, lock_file: Path) -> None:
        self.process = process
        self.lock_file = lock_file
        super().__init__(f"Process '{process}' has already been started. " f"Lock file: {lock_file}")


class ProcessLock:
    def __init__(self, save_dir: Path | str, process: str) -> None:
        self.save_dir = Path(save_dir)
        self.process = process
        self.lock_file = self.save_dir / f"{process}_in_progress.lock"

    def __enter__(self) -> "ProcessLock":
        self.raise_for_in_process()
        self.lock_file.touch()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> False:
        self.lock_file.unlink(missing_ok=True)
        return False  # do not suppress exceptions

    def raise_for_in_process(self) -> None:
        if self.lock_file.exists():
            raise ProcessRunning(self.process, self.lock_file)


def get_status_file(save_dir: Path | str, process: str) -> Path:
    return Path(save_dir) / f"last_{process}.json"


def get_status_file_content(save_dir: Path | str, process: str) -> Dict[str, Any]:
    status_file = get_status_file(save_dir, process)

    with status_file.open("r") as f:
        return json.load(f)
