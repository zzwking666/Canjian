"""
独立系统资源探针：不做任何其他事，只循环打印 CPU 与内存占用。
用途：在 MaixCam 开机后单独运行本脚本，观察系统自身（不含主程序）的基线占用。

用法：
    python sys_resource_probe.py            # 每 1 秒打印一次
    python sys_resource_probe.py 0.2        # 指定打印间隔（秒）

Ctrl+C 退出。
"""
import sys
import time


def read_cpu_times():
    """返回 (idle, total) jiffies；读取失败返回 None。"""
    try:
        with open("/proc/stat", "r") as f:
            parts = f.readline().split()
        values = [int(v) for v in parts[1:]]
        idle = values[3] + (values[4] if len(values) > 4 else 0)  # idle + iowait
        return idle, sum(values)
    except Exception:
        return None


def read_mem_usage():
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


def main():
    interval = 1.0
    if len(sys.argv) > 1:
        try:
            interval = max(0.05, float(sys.argv[1]))
        except ValueError:
            pass

    print("系统资源基线探针，间隔 %.2fs，Ctrl+C 退出" % interval)
    prev_cpu = None
    try:
        while True:
            t0 = time.monotonic()

            cpu = read_cpu_times()
            if cpu is not None and prev_cpu is not None:
                idle_d = cpu[0] - prev_cpu[0]
                total_d = cpu[1] - prev_cpu[1]
                cpu_str = "%.1f%%" % (max(0.0, 1.0 - idle_d / total_d) * 100) if total_d > 0 else "N/A"
            else:
                cpu_str = "N/A"  # 首个采样点无差值，或读取失败
            if cpu is not None:
                prev_cpu = cpu

            mem = read_mem_usage()
            if mem is not None:
                used_mb, total_mb = mem[0] // 1024, mem[1] // 1024
                mem_str = "%.1f%% (%d/%d MB)" % (mem[0] * 100.0 / mem[1], used_mb, total_mb)
            else:
                mem_str = "N/A"

            print("[基线] CPU %s | 内存 %s" % (cpu_str, mem_str))

            elapsed = time.monotonic() - t0
            time.sleep(max(0.0, interval - elapsed))
    except KeyboardInterrupt:
        print("\n已退出")


if __name__ == "__main__":
    main()
