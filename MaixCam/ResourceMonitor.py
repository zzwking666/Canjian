"""
实时资源监控：守护线程每隔约 200ms 打印一次 CPU 与内存占用。

- CPU：读取 /proc/stat 第一行 jiffies 差值计算（idle+iowait 占比取反）
- 内存：读取 /proc/meminfo，(MemTotal - MemAvailable) / MemTotal
- 非 Linux 环境（如 Windows 开发机）读取失败时打印 N/A，不影响主程序
"""
import threading
import time


class ResourceMonitor:
    _instance = None
    _instance_lock = threading.Lock()

    INTERVAL_S = 0.2  # 打印间隔

    def __init__(self):
        self._thread = None
        self._stop_event = threading.Event()

    @classmethod
    def instance(cls):
        # 双重检查锁单例，与 TaskGPIOManager 保持一致
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    @staticmethod
    def _read_cpu_times():
        """返回 (idle, total) jiffies；读取失败返回 None。"""
        try:
            with open("/proc/stat", "r") as f:
                parts = f.readline().split()
            values = [int(v) for v in parts[1:]]
            idle = values[3] + (values[4] if len(values) > 4 else 0)  # idle + iowait
            return idle, sum(values)
        except Exception:
            return None

    @staticmethod
    def _read_mem_usage():
        """返回 (used_kb, total_kb)；读取失败返回 None。"""
        try:
            info = {}
            with open("/proc/meminfo", "r") as f:
                for line in f:
                    key, _, rest = line.partition(":")
                    info[key.strip()] = int(rest.strip().split()[0])
            total = info["MemTotal"]
            used = total - info.get("MemAvailable", info.get("MemFree", 0))
            return used, total
        except Exception:
            return None

    def _run(self):
        prev_cpu = None
        while not self._stop_event.is_set():
            t0 = time.monotonic()

            cpu = self._read_cpu_times()
            if cpu is not None and prev_cpu is not None:
                idle_d = cpu[0] - prev_cpu[0]
                total_d = cpu[1] - prev_cpu[1]
                cpu_str = "%.1f%%" % (max(0.0, 1.0 - idle_d / total_d) * 100) if total_d > 0 else "N/A"
            else:
                cpu_str = "N/A"  # 首个采样点无差值，或读取失败
            if cpu is not None:
                prev_cpu = cpu

            mem = self._read_mem_usage()
            if mem is not None:
                used_mb, total_mb = mem[0] // 1024, mem[1] // 1024
                mem_str = "%.1f%% (%d/%d MB)" % (mem[0] * 100.0 / mem[1], used_mb, total_mb)
            else:
                mem_str = "N/A"

            print("[监控] CPU %s | 内存 %s" % (cpu_str, mem_str))

            # 扣除本次采样耗时，保证打印间隔接近 INTERVAL_S
            elapsed = time.monotonic() - t0
            self._stop_event.wait(max(0.0, self.INTERVAL_S - elapsed))

    def start(self):
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, name="ResourceMonitor", daemon=True)
        self._thread.start()

    def stop(self, timeout=1.0):
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=timeout)
            self._thread = None
