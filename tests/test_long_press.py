"""
MLongPressButton 长按逻辑仿真测试。

通过 stub maix 模块，在本机模拟 MaixCam 触摸屏驱动的真实行为：
- hyn_ts 驱动是事件驱动的，但 read() 会返回缓存状态，
  即按住不动期间每帧都返回 (last_x, last_y, pressed=1) —— 电平式上报。
- 模拟完整控件链：MTabWidget -> MTabPage -> MLongPressButton。
"""
import sys
import types

# ---------------- stub maix 模块（必须在导入 Mt 组件前完成） ----------------
# 统一使用共享 stub，避免与其它测试文件的 sys.modules.setdefault 互相覆盖
import maix_stub

maix_stub.install()
_current_ms = maix_stub.current_ms

# ---------------------------------------------------------------------------

from Mt.MLongPressButton import MLongPressButton


def _make_button():
    btn = MLongPressButton(text="关机", x=530, y=290, w=100, h=100, long_press_ms=1000)
    fired = []
    btn.long_pressed.connect(lambda: fired.append(_current_ms[0]))
    return btn, fired


def _advance(ms):
    _current_ms[0] += ms


def test_long_press_fires_while_holding():
    """按住 1 秒后（不松手）应触发 long_pressed。"""
    btn, fired = _make_button()
    # 第 0 帧：按下
    btn.hit_test(560, 320, True)
    # 之后每 16ms 一帧，持续按住（电平式上报 pressed=1）
    for _ in range(70):  # 70 * 16ms ≈ 1120ms
        _advance(16)
        btn.hit_test(560, 320, True)
        if fired:
            break
    assert fired, "长按 1 秒应触发 long_pressed"
    # 触发时间点应在 1000ms 附近（16ms 帧粒度）
    assert 1000 <= fired[0] <= 1100, f"触发时间 {fired[0]} 不在预期范围"
    # 只触发一次
    for _ in range(20):
        _advance(16)
        btn.hit_test(560, 320, True)
    assert len(fired) == 1, "长按只应触发一次"


def test_short_press_does_not_fire():
    """短按（300ms 后松开）不应触发。"""
    btn, fired = _make_button()
    btn.hit_test(560, 320, True)
    for _ in range(20):  # 300ms
        _advance(16)
        btn.hit_test(560, 320, True)
    _advance(16)
    btn.hit_test(560, 320, False)  # 松开
    assert not fired, "短按不应触发 long_pressed"


def test_slide_out_cancels():
    """按住后滑出按钮区域应取消；重新按下后长按仍能触发。"""
    btn, fired = _make_button()
    btn.hit_test(560, 320, True)
    for _ in range(10):
        _advance(16)
        btn.hit_test(560, 320, True)
    # 手指滑出按钮区域但仍按住
    for _ in range(70):
        _advance(16)
        btn.hit_test(100, 100, True)
    assert not fired, "滑出按钮后不应触发"
    # 松开后重新长按，依然可用
    btn.hit_test(100, 100, False)
    btn.hit_test(560, 320, True)
    for _ in range(70):
        _advance(16)
        btn.hit_test(560, 320, True)
        if fired:
            break
    assert fired, "重新长按应能再次触发"


def test_repeat_long_press():
    """完成一次长按后，下一次长按仍可触发。"""
    btn, fired = _make_button()
    for _ in range(2):
        btn.hit_test(560, 320, True)
        for _ in range(70):
            _advance(16)
            btn.hit_test(560, 320, True)
        btn.hit_test(560, 320, False)  # 松开
        _advance(16)
    assert len(fired) == 2, f"两次长按都应触发，实际 {len(fired)} 次"


def test_release_fallback_after_stall():
    """按住期间主循环卡顿（计时帧缺失），松开时已超 1s，应补触发。"""
    btn, fired = _make_button()
    btn.hit_test(560, 320, True)
    _advance(1200)              # 模拟 1.2s 内没有新帧（卡顿）
    btn.hit_test(560, 320, False)  # 直接松开
    assert len(fired) == 1, "按住超 1s 后松开应补触发"
