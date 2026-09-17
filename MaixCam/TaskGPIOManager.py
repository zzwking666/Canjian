"""TaskGPIOManager

Provides TaskGPIOManager class and module-level convenience wrappers:
- startTaskManager()
- stopTaskManager(timeout)
- pushTask(high_ms, low_ms, delay_ms)
- clearTask()

This module depends on `MaixCam.Modules.Modules` to control GPIO.
"""
from typing import NamedTuple
import threading
import queue
import time

from MaixCam.Modules import Modules
from MaixCam.RunningInfo import DouMode,RunningInfo
from MaixCam.Action import setDaDouStatus, setXiaoDouStatus


class GPIOTask(NamedTuple):
    high_ms: int
    low_ms: int
    dou_mode: DouMode
    delay_ms: int = 0


class TaskGPIOManager:
    """Thread-safe singleton TaskGPIOManager.

    You can obtain the singleton either by calling TaskGPIOManager.instance()
    or by instantiating TaskGPIOManager() (both return the same object).
    """
    _instance = None
    _instance_lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        # Double-checked locking for singleton
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = super(TaskGPIOManager, cls).__new__(cls)
        return cls._instance

    @classmethod
    def instance(cls):
        """Return the singleton instance.

        Convenience method; equivalent to TaskGPIOManager().
        """
        return cls()

    def __init__(self):
        # __init__ may be called multiple times in singleton pattern; guard actual
        # initialization so we don't re-create internal structures.
        if getattr(self, "_initialized", False):
            return
        # single-task executor state
        self._thread = None
        self._stop_event = None
        # previous queue-based model removed; keep lock for synchronization
        self._lock = threading.Lock()
        # enabled flag: when False, pushTask will be ignored
        self._enabled = True
        self._initialized = True

    def _run_task(self, task: GPIOTask, stop_event: threading.Event):
        """Run a single task. This method blocks until the task completes or
        stop_event is set. It's intended to be run inside a dedicated thread.
        """
        # optional initial delay before executing this task
        if task.delay_ms > 0:
            if stop_event.wait(task.delay_ms / 1000.0):
                return

        if task.dou_mode == DouMode.DaDouOnly:
            # open
            setDaDouStatus(True)
            setXiaoDouStatus(False)
            if stop_event.wait(task.high_ms / 1000.0):
                return

            # close
            setDaDouStatus(False)
            if stop_event.wait(task.low_ms / 1000.0):
                return
        elif task.dou_mode == DouMode.XiaoDouOnly:
            # open
            setDaDouStatus(False)
            setXiaoDouStatus(True)
            if stop_event.wait(task.high_ms / 1000.0):
                return

            # close
            setXiaoDouStatus(False)
            if stop_event.wait(task.low_ms / 1000.0):
                return
        elif task.dou_mode == DouMode.BothDaDouXiaoDou:
            # open
            setDaDouStatus(True)
            setXiaoDouStatus(True)
            if stop_event.wait(task.high_ms / 1000.0):
                return

            # close
            setDaDouStatus(False)
            setXiaoDouStatus(False)
            if stop_event.wait(task.low_ms / 1000.0):
                return
        else:
            setDaDouStatus(False)
            setXiaoDouStatus(False)
            total_ms = task.high_ms + task.low_ms
            if stop_event.wait(total_ms / 1000.0):
                return

    def startTaskManager(self):
        """Start the background consumer thread. No-op if already running."""
        # For single-task executor we interpret start as enabling the manager.
        with self._lock:
            self._enabled = True

    def stopTaskManager(self, timeout: float = 1.0):
        """Signal the worker to stop and join the thread."""
        with self._lock:
            # disable manager so new pushes are ignored
            self._enabled = False
            # stop any currently running task
            if self._stop_event:
                self._stop_event.set()
            if self._thread:
                self._thread.join(timeout=timeout)
            self._thread = None
            self._stop_event = None

    def pushTask(self, high_ms: int = 1200, low_ms: int = 300, mode: DouMode = DouMode.Stop, delay_ms: int = 0):
        """Execute the given task immediately.

        If a previous task is still running, it will be forcefully stopped before
        the new task starts.
        """
        if not self._enabled:
            return

        task = GPIOTask(high_ms, low_ms, mode, delay_ms)

        with self._lock:
            # if a task is running, signal it to stop and wait shortly
            if self._stop_event:
                try:
                    self._stop_event.set()
                except Exception:
                    pass
            if self._thread:
                try:
                    self._thread.join(timeout=0.5)
                except Exception:
                    pass
                self._thread = None
                self._stop_event = None

            # start a new thread to run this task
            stop_event = threading.Event()
            t = threading.Thread(target=self._run_task, args=(task, stop_event), daemon=True)
            self._stop_event = stop_event
            self._thread = t
            t.start()

    def clearTask(self):
        """Remove all pending tasks from the queue."""
        # No-op for single-task executor; stop currently running task if any
        with self._lock:
            if self._stop_event:
                try:
                    self._stop_event.set()
                except Exception:
                    pass
            if self._thread:
                try:
                    self._thread.join(timeout=0.5)
                except Exception:
                    pass
                self._thread = None
                self._stop_event = None

    def is_running(self) -> bool:
        return bool(self._thread and self._thread.is_alive())

