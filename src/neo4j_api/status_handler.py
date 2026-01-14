"""status handler module for data upload"""

import json
from pathlib import Path


class ProcessRunning(Exception):
    def __init__(self, process: str, lock_file: Path):
        self.process = process
        self.lock_file = lock_file

    def __str__(self):
        return f"Process {self.process} has already been started. Lock file is {self.lock_file}"


class ProcessLock:
    def __init__(self, save_dir, process):
        self.save_dir = Path(save_dir)
        self.process = process
        self.lock_file = self.save_dir / f"{process}_in_progress.lock"

    def __enter__(self):
        self.raise_for_in_process()
        self.lock_file.touch()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.lock_file.exists():
            self.lock_file.unlink()
        return False

    def raise_for_in_process(self):
        if self.lock_file.exists():
            raise ProcessRunning(self.process, self.lock_file)


def get_status_file(save_dir, process):
    return save_dir / f"last_{process}.json"


def get_status_file_content(save_dir, process):
    with open(get_status_file(save_dir, process), "r") as f:
        content = json.load(f)
    return content
