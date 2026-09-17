from maix import image, time
from Mt.MPushButton import MPushButton
from Mt.MWidget import mark_dirty
from Mt.MSignal import MSignal

class MLongPressButton(MPushButton):
    """
    长按按钮：按住达到 long_press_ms 毫秒后才触发 long_pressed 信号，
    短按不触发任何操作（普通 clicked 信号被屏蔽）。
    按住期间按钮底色变暗作为视觉反馈。
    """
    # 调试开关：True 时打印按下/触发日志，便于在 MaixVision 控制台排查
    DEBUG = True

    def __init__(self, text, x, y, w, h, parent=None, long_press_ms=1000):
        super().__init__(text, x, y, w, h, parent)
        self.long_press_ms = long_press_ms
        self.long_pressed = MSignal()
        self._press_start_ms = 0
        self._long_fired = False
        self._normal_bg_color = self.bg_color
        self._pressing_bg_color = image.Color.from_rgb(200, 200, 200)

    @staticmethod
    def _elapsed_ms(now, start):
        # 注意：maix.time.ticks_diff(last, now) 的参数顺序与 MicroPython 相反，
        # 且 ticks_ms 基于 CLOCK_MONOTONIC 单调递增、不会回绕，直接相减即可。
        return now - start

    def hit_test(self, x, y, pressed=None):
        if not self.isVisible():
            return None
        inside = self.x <= x < self.x + self.w and self.y <= y < self.y + self.h
        if pressed is None:
            return self if inside else None

        if inside:
            if pressed:
                now = time.ticks_ms()
                if not self._pressed:
                    # 刚按下：记录起始时间
                    self._pressed = True
                    mark_dirty()  # 底色变暗，需要重绘
                    self._press_start_ms = now
                    self._long_fired = False
                    if self.DEBUG:
                        print("[MLongPressButton] 按下，开始计时", self._text)
                elif not self._long_fired and self._elapsed_ms(now, self._press_start_ms) >= self.long_press_ms:
                    # 持续按住达到阈值：触发长按信号，只触发一次
                    self._long_fired = True
                    if self.DEBUG:
                        print("[MLongPressButton] 长按", self.long_press_ms, "ms 触发", self._text)
                    self.long_pressed.emit()
                return None
            else:
                # 松开：短按不触发 clicked；
                # 兜底：若按住已达到阈值但尚未触发（例如主循环卡顿错过计时帧），松开时补触发
                was_pressed = self._pressed
                held_ms = self._elapsed_ms(time.ticks_ms(), self._press_start_ms) if was_pressed else 0
                should_fire = was_pressed and not self._long_fired and held_ms >= self.long_press_ms
                self._pressed = False
                if was_pressed:
                    mark_dirty()  # 底色恢复，需要重绘
                self._press_start_ms = 0
                self._long_fired = False
                if self.DEBUG and was_pressed:
                    print("[MLongPressButton] 松开，实际按住", held_ms, "ms", self._text)
                if should_fire:
                    if self.DEBUG:
                        print("[MLongPressButton] 松开时补触发", self._text)
                    self.long_pressed.emit()
                return self if was_pressed else None
        else:
            # 手指移出按钮区域：取消本次按压
            if self._pressed:
                mark_dirty()  # 底色恢复，需要重绘
            self._pressed = False
            self._press_start_ms = 0
            self._long_fired = False
        return None

    def paintEvent(self, img):
        # 按住期间切换为暗色底色，提供按压反馈
        self.bg_color = self._pressing_bg_color if self._pressed else self._normal_bg_color
        super().paintEvent(img)
