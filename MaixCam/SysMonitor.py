"""
整机/本进程 CPU 与内存占用采样（基于 Linux /proc）。

- 整机 CPU：/proc/stat 两次采样差值计算占用百分比
- 整机内存：/proc/meminfo 的 MemTotal / MemAvailable
- 进程 CPU：/proc/self/stat 的 utime+stime 差值 / 墙钟时间（多核可超过 100%）
- 进程内存：/proc/self/status 的 VmRSS

在非 Linux 环境（如本机仿真测试）读 /proc 失败时，指标保持 None，
format() 以 "--" 占位，不影响主流程。
"""
import os
import time


class SysMonitor:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(SysMonitor, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if getattr(self, "_initialized", False):
            return
        self._initialized = True
        # 最近一次采样结果（百分比 / MB），None 表示暂无数据
        self.cpu_sys = None
        self.mem_sys = None
        self.cpu_proc = None
        self.rss_mb = None
        # 上一次采样快照（CPU 百分比需两次采样求差值）
        self._prev_cpu = None    # (busy, total)
        self._prev_proc = None   # (proc_ticks, wall_seconds)
        try:
            self._clk_tck = os.sysconf("SC_CLK_TCK")
        except Exception:
            self._clk_tck = 100

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    # ------------------------------------------------------------------
    # /proc 读取
    # ------------------------------------------------------------------
    @staticmethod
    def _read_cpu_times():
        """返回 (busy, total)，单位 jiffies。"""
        with open("/proc/stat", "r") as f:
            parts = f.readline().split()
        if not parts or parts[0] != "cpu":
            raise ValueError("bad /proc/stat")
        vals = [int(x) for x in parts[1:11]]
        idle = vals[3] + (vals[4] if len(vals) > 4 else 0)  # idle + iowait
        total = sum(vals)
        return total - idle, total

    @staticmethod
    def _read_meminfo():
        """返回 (MemTotal_kb, MemAvailable_kb)。"""
        total = avail = None
        with open("/proc/meminfo", "r") as f:
            for line in f:
                if line.startswith("MemTotal:"):
                    total = int(line.split()[1])
                elif line.startswith("MemAvailable:"):
                    avail = int(line.split()[1])
                if total is not None and avail is not None:
                    break
        if not total or avail is None:
            raise ValueError("bad /proc/meminfo")
        return total, avail

    @staticmethod
    def _read_proc_ticks():
        """本进程 utime+stime，单位 clock ticks。"""
        with open("/proc/self/stat", "r") as f:
            s = f.read()
        # comm 可能含空格/括号，从最后一个 ')' 之后开始按列解析：
        # rest[0] 为第 3 列 state，因此第 14/15 列 utime/stime 对应 rest[11]/rest[12]
        rest = s[s.rfind(")") + 2:].split()
        return int(rest[11]) + int(rest[12])

    @staticmethod
    def _read_rss_kb():
        with open("/proc/self/status", "r") as f:
            for line in f:
                if line.startswith("VmRSS:"):
                    return int(line.split()[1])
        raise ValueError("no VmRSS")

    # ------------------------------------------------------------------
    # 采样与格式化
    # ------------------------------------------------------------------
    def sample(self):
        """采样一次并更新指标；读 /proc 失败时保持旧值。CPU 百分比需两次采样后才有值。"""
        try:
            busy, total = self._read_cpu_times()
            if self._prev_cpu is not None:
                d_busy = busy - self._prev_cpu[0]
                d_total = total - self._prev_cpu[1]
                if d_total > 0:
                    self.cpu_sys = d_busy * 100.0 / d_total
            self._prev_cpu = (busy, total)
        except Exception:
            pass

        try:
            total_kb, avail_kb = self._read_meminfo()
            self.mem_sys = (total_kb - avail_kb) * 100.0 / total_kb
        except Exception:
            pass

        try:
            ticks = self._read_proc_ticks()
            now = time.time()
            if self._prev_proc is not None:
                d_ticks = ticks - self._prev_proc[0]
                d_sec = now - self._prev_proc[1]
                if d_sec > 0:
                    self.cpu_proc = (d_ticks / self._clk_tck) / d_sec * 100.0
            self._prev_proc = (ticks, now)
        except Exception:
            pass

        try:
            self.rss_mb = self._read_rss_kb() / 1024.0
        except Exception:
            pass

    def format(self):
        """两行紧凑文本：整机 CPU%/内存% + 本进程 CPU%/RSS；无数据显示 --。"""
        def pct(v):
            return "--" if v is None else f"{v:.0f}%"

        line1 = f"CPU {pct(self.cpu_sys)} MEM {pct(self.mem_sys)}"
        rss = "--" if self.rss_mb is None else f"{self.rss_mb:.0f}MB"
        line2 = f"APP {pct(self.cpu_proc)} {rss}"
        return f"{line1}\n{line2}"
