from maix import image
from Mt.MWidget import MWidget, mark_dirty
from Mt.MSignal import MSignal

class MPushButton(MWidget):
    # 文字缩放上限：普通按钮不放大（1.0），数字键盘等大按钮可设为 2.0
    text_scale_max = 1.0
    # 文字缩放下限：再小就不可读了
    text_scale_min = 0.4

    def __init__(self, text, x, y, w, h, parent=None):
        super().__init__(x, y, w, h, parent)
        self._text = text
        self.bg_color = image.Color.from_rgb(240,240,240)
        self.border_color = image.Color.from_rgb(180,180,180)
        self.text_color = image.Color.from_rgb(0,0,0)
        self.clicked = MSignal()
    @staticmethod
    def measure_text(text):
        try:
            size = image.string_size(text)
            return size.width(), size.height()
        except Exception:
            return len(text) * 8, 16

    @classmethod
    def wrap_text(cls, text, max_width, padding=8):
        if text is None:
            return [""]

        max_width = max(1, max_width - padding * 2)
        lines = []
        for paragraph in str(text).splitlines() or [""]:
            if paragraph == "":
                lines.append("")
                continue

            current = ""
            for word in paragraph.split(" "):
                candidate = word if not current else current + " " + word
                if cls.measure_text(candidate)[0] <= max_width:
                    current = candidate
                    continue

                if current:
                    lines.append(current)

                if cls.measure_text(word)[0] <= max_width:
                    current = word
                    continue

                chunk = ""
                for ch in word:
                    next_chunk = chunk + ch
                    if chunk and cls.measure_text(next_chunk)[0] > max_width:
                        lines.append(chunk)
                        chunk = ch
                    else:
                        chunk = next_chunk
                current = chunk

            if current:
                lines.append(current)

        return lines or [""]

    @classmethod
    def text_block_height(cls, text, max_width, padding=8, line_gap=4):
        lines = cls.wrap_text(text, max_width, padding=padding)
        _, line_height = cls.measure_text("Ag")
        line_height = max(16, line_height)
        return len(lines) * line_height + max(0, len(lines) - 1) * line_gap + padding * 2
    def setText(self, text):
        if self._text != text:
            self._text = text
            mark_dirty()
    def text(self):
        return self._text
    def _fit_scale(self, lines, line_height, padding=8, line_gap=4):
        """计算让文字块完整放进按钮的最大缩放系数。

        先看 scale=1 时是否放得下，放不下则按比例缩小（不小于 text_scale_min），
        放得下且 text_scale_max > 1 时允许适当放大。
        """
        avail_w = max(1, self.w - padding * 2)
        avail_h = max(1, self.h - padding * 2)
        max_line_w = max((self.measure_text(l)[0] for l in lines), default=0)
        block_h = len(lines) * line_height + max(0, len(lines) - 1) * line_gap
        if max_line_w <= 0 or block_h <= 0:
            return 1.0
        scale = min(avail_w / max_line_w, avail_h / block_h)
        if scale >= 1.0:
            # 空间富余：允许放大到 text_scale_max，但不强行铺满；
            # text_scale_max < 1.0 时反向生效——空间够也按上限缩小（用于调小按钮字号）
            return max(min(self.text_scale_max, 1.0), min(self.text_scale_max, scale))
        return max(self.text_scale_min, scale)

    def _layout_lines(self, line_height):
        """选择可读性最好的排版：单行缩放 vs 换行，取缩放系数更大者。

        英/越语文本略超宽时，缩小单行比拆成两行更小字体更清晰。
        """
        text = str(self._text)
        avail_w = max(1, self.w - 16)
        if "\n" in text:
            # 显式换行的文本按原样分行，保持单词完整（不把 "Power" 拆成 "Powe"/"r"），
            # 宽度不够时由 _fit_scale 整体缩小适配
            lines = text.splitlines() or [""]
            return lines, self._fit_scale(lines, line_height)
        full_w, _ = self.measure_text(text)
        if full_w > avail_w:
            single_scale = avail_w / max(1, full_w)
            wrapped = self.wrap_text(text, self.w, padding=8)
            wrap_scale = self._fit_scale(wrapped, line_height)
            if single_scale >= wrap_scale:
                return [text], max(self.text_scale_min, min(1.0, single_scale))
        wrapped = self.wrap_text(text, self.w, padding=8)
        return wrapped, self._fit_scale(wrapped, line_height)

    @staticmethod
    def _draw_string_scaled(img, x, y, text, color, scale):
        """draw_string 的 scale 参数兼容封装：不支持 scale 的旧固件退化为原大小。"""
        if abs(scale - 1.0) < 1e-3:
            img.draw_string(x, y, text, color)
            return
        try:
            img.draw_string(x, y, text, color, scale=scale)
        except TypeError:
            img.draw_string(x, y, text, color)

    def paintEvent(self, img):
        if not self.isVisible():
            return
        img.draw_rect(self.x, self.y, self.w, self.h, self.bg_color, thickness=-1)
        img.draw_rect(self.x, self.y, self.w, self.h, self.border_color, thickness=2)
        _, line_height = self.measure_text("Ag")
        line_height = max(16, line_height)
        lines, scale = self._layout_lines(line_height)
        scaled_line_h = int(line_height * scale)
        scaled_gap = max(1, int(4 * scale))
        text_height = len(lines) * scaled_line_h + max(0, len(lines) - 1) * scaled_gap
        start_y = self.y + max(0, (self.h - text_height) // 2)

        for index, line in enumerate(lines):
            line_width, _ = self.measure_text(line)
            line_width = int(line_width * scale)
            line_x = self.x + max(0, (self.w - line_width) // 2)
            line_y = start_y + index * (scaled_line_h + scaled_gap)
            self._draw_string_scaled(img, line_x, line_y, line, self.text_color, scale)
    def hit_test(self, x, y, pressed=None):
        if not self.isVisible():
            return None
        if self.x <= x < self.x + self.w and self.y <= y < self.y + self.h:
            if pressed is not None:
                if pressed and not getattr(self, "_pressed", False):
                    self._pressed = True
                elif not pressed and getattr(self, "_pressed", False):
                    self._pressed = False
                    self.clicked.emit()
                    return self
                return None
            else:
                return self
        else:
            self._pressed = False
        return None