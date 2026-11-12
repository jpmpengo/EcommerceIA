import msvcrt
from contextlib import contextmanager

from django.conf import settings


@contextmanager
def supplier_monitor_lock():
    path = settings.BASE_DIR / "supplier_monitor.lock"
    with open(path, "a+b") as lock_file:
        lock_file.seek(0)
        lock_file.write(b"0")
        lock_file.flush()
        lock_file.seek(0)
        try:
            msvcrt.locking(lock_file.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError:
            yield False
        else:
            try:
                yield True
            finally:
                lock_file.seek(0)
                msvcrt.locking(lock_file.fileno(), msvcrt.LK_UNLCK, 1)
