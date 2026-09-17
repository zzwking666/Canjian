"""
共享的 maix 模块 stub，供需要在本机仿真 Mt/MaixCam 控件的测试使用。

用法（必须在导入任何 Mt/MaixCam 组件前完成）：
    import maix_stub
    maix_stub.install()

说明：
- 多个测试文件若各自 stub maix 并 setdefault 进 sys.modules，先加载者的
  ticks_ms 会一直生效，导致后加载的测试时间推进失效。统一在这里 stub，
  时间通过共享的 current_ms 单元推进：
      maix_stub.current_ms[0] += 1000  # 前进 1 秒
- string_size 模拟 32px 字体：按行测量，每字符宽 16，行高 32。
"""
import sys
import types

# 共享时间单元（毫秒），测试通过修改 current_ms[0] 推进时间
current_ms = [0]


class FakeSize:
    def __init__(self, w, h):
        self._w, self._h = w, h
    def width(self):
        return self._w
    def height(self):
        return self._h


class FakeColor:
    @staticmethod
    def from_rgb(r, g, b):
        return (r, g, b)


def fake_string_size(text):
    lines = str(text).splitlines() or [""]
    w = max((len(line) for line in lines), default=0) * 16
    h = len(lines) * 32
    return FakeSize(w, h)


def install():
    """把假的 maix 模块族装入 sys.modules（幂等）。"""
    fake_image = types.ModuleType("maix.image")
    fake_image.Color = FakeColor
    fake_image.string_size = fake_string_size
    fake_image.Fit = types.SimpleNamespace(FIT_CONTAIN=0)

    fake_time = types.ModuleType("maix.time")

    def _ticks_ms():
        return current_ms[0]

    def _ticks_diff(last, now):
        # 与真实 maix.time.ticks_diff(last, now) 保持一致：返回 now - last
        return now - last

    fake_time.ticks_ms = _ticks_ms
    fake_time.ticks_diff = _ticks_diff

    fake_maix = types.ModuleType("maix")
    fake_maix.image = fake_image
    fake_maix.time = fake_time
    for name in ("touchscreen", "app", "display", "gpio", "nn", "camera"):
        sub = types.ModuleType(f"maix.{name}")
        setattr(fake_maix, name, sub)
        sys.modules.setdefault(f"maix.{name}", sub)

    sys.modules.setdefault("maix", fake_maix)
    sys.modules.setdefault("maix.image", fake_image)
    sys.modules.setdefault("maix.time", fake_time)
    return fake_maix
