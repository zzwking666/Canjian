"""
资源监控（SysMonitor）与运行页监控角标布局的仿真测试。

- SysMonitor.format()：无采样数据时以 "--" 占位，输出两行；
- SysMonitor.sample()：本机（无 /proc）调用不抛异常，指标保持 None；
- 运行页 sysInfoLabel：在页面范围内，不与相机画面/执行状态/GPIO 指示灯重叠，
  且缩放后的文本块宽度不超出标签宽度。
"""
import sys
import types
import unittest

# 统一使用共享 stub（必须在导入 Mt/MaixCam 组件前完成）
import maix_stub

maix_stub.install()

from MaixCam.Config import Config  # 纯 python，可直接用

_fake_modules_mod = types.ModuleType("MaixCam.Modules")


class _FakeModules:
    _inst = None

    @classmethod
    def instance(cls):
        if cls._inst is None:
            cls._inst = cls()
        return cls._inst

    def __init__(self):
        self.config = Config()
        self.paths = types.SimpleNamespace(config_path="")
        self.sysInfoLabel = None


_fake_modules_mod.Modules = _FakeModules
sys.modules["MaixCam.Modules"] = _fake_modules_mod

_fake_gpio_mod = types.ModuleType("MaixCam.TaskGPIOManager")


class _FakeTaskGPIOManager:
    _inst = None

    @classmethod
    def instance(cls):
        if cls._inst is None:
            cls._inst = cls()
        return cls._inst

    def startTaskManager(self):
        pass

    def stopTaskManager(self):
        pass

    def clearTask(self):
        pass


_fake_gpio_mod.TaskGPIOManager = _FakeTaskGPIOManager
sys.modules["MaixCam.TaskGPIOManager"] = _fake_gpio_mod

_fake_action_mod = types.ModuleType("MaixCam.Action")
_fake_action_mod.setDaDouStatus = lambda on: None
_fake_action_mod.setXiaoDouStatus = lambda on: None
sys.modules["MaixCam.Action"] = _fake_action_mod

# ---------------------------------------------------------------------------

from MaixCam.MainWindow import MaixCamMainWindow
from MaixCam.SysMonitor import SysMonitor

SCREEN_W, SCREEN_H = 640, 480


def _rect(w):
    return (w.x, w.y, w.x + w.w, w.y + w.h)


def _overlap(a, b):
    ax0, ay0, ax1, ay1 = _rect(a)
    bx0, by0, bx1, by1 = _rect(b)
    return ax0 < bx1 and bx0 < ax1 and ay0 < by1 and by0 < ay1


class TestSysMonitor(unittest.TestCase):
    def test_format_without_data(self):
        mon = SysMonitor()
        mon.cpu_sys = mon.mem_sys = mon.cpu_proc = mon.rss_mb = None
        lines = mon.format().splitlines()
        self.assertEqual(len(lines), 2)
        self.assertIn("--", lines[0])
        self.assertIn("--", lines[1])

    def test_format_with_data(self):
        mon = SysMonitor()
        mon.cpu_sys, mon.mem_sys, mon.cpu_proc, mon.rss_mb = 35.4, 62.6, 28.0, 120.4
        self.assertEqual(mon.format(), "CPU 35% MEM 63%\nAPP 28% 120MB")

    def test_sample_never_raises(self):
        # 本机无 /proc 时采样应静默失败且不抛异常
        mon = SysMonitor()
        mon.sample()
        mon.sample()


class TestSysInfoLabelLayout(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.win = MaixCamMainWindow(0, 0, SCREEN_W, SCREEN_H, margin=0)

    def test_label_within_page_and_no_overlap(self):
        w = self.win
        lb = w.sysInfoLabel
        container = w.releaseContainer
        # 在页面范围内
        self.assertGreaterEqual(lb.x, 0)
        self.assertGreaterEqual(lb.y, 0)
        self.assertLessEqual(lb.x + lb.w, container.w)
        self.assertLessEqual(lb.y + lb.h, container.h)
        # 不与底部状态控件重叠（相机画面为全屏底图，控件叠加在上层属设计行为）
        self.assertFalse(_overlap(lb, w.actuatorStatus))
        self.assertFalse(_overlap(lb, w.gpioStatus))
        # 不与右侧按钮列重叠
        for btn in (w.exit_release_btn, w.countButtonRun, w.douStatus,
                    w.triggerCircleLabel_ms, w.btn_shutdown):
            self.assertFalse(_overlap(lb, btn))

    def test_label_text_fits(self):
        # 最宽文本（两个 100%）经 MLabel 自适应缩小后也不超出标签区域
        lb = self.win.sysInfoLabel
        mon = SysMonitor()
        mon.cpu_sys, mon.mem_sys, mon.cpu_proc, mon.rss_mb = 100.0, 100.0, 100.0, 999.9
        text = mon.format()
        text_w, text_h = lb._measure_text_block(text)
        scale = max(lb.text_scale_min,
                    min(lb.w / (text_w + 4), lb.h / (text_h + 4), 1.0))
        self.assertLessEqual(int(text_w * scale) + 2, lb.w)
        self.assertLessEqual(int(text_h * scale), lb.h)


if __name__ == "__main__":
    unittest.main()
