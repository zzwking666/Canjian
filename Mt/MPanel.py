from maix import image
from Mt.MWidget import MWidget


class MPanel(MWidget):
    """
    纯装饰面板：绘制带边框的底色矩形（标题栏、卡片底等）。
    不响应任何触摸事件，事件穿透给其它控件。
    """

    def __init__(self, x, y, w, h, bg_color=None, border_color=None, parent=None):
        super().__init__(x, y, w, h, parent)
        self.bg_color = bg_color or image.Color.from_rgb(248, 249, 251)
        self.border_color = border_color or image.Color.from_rgb(210, 214, 220)

    def paintEvent(self, img):
        if not self.isVisible():
            return
        img.draw_rect(self.x, self.y, self.w, self.h, self.bg_color, thickness=-1)
        img.draw_rect(self.x, self.y, self.w, self.h, self.border_color, thickness=1)

    def hit_test(self, x, y, pressed=None):
        # 装饰控件，永不拦截触摸
        return None
