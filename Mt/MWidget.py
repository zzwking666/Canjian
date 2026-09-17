from maix import image

# 全局重绘请求标记：控件状态变化时置位，主循环据此跳过无变化的整屏重绘。
# 初始为 True，保证启动后第一帧一定绘制。
_need_repaint = True


def mark_dirty():
    """控件内容发生变化时调用，请求下一帧重绘。"""
    global _need_repaint
    _need_repaint = True


def consume_repaint_request():
    """主循环消费一次重绘请求：返回当前标记并清零。"""
    global _need_repaint
    dirty = _need_repaint
    _need_repaint = False
    return dirty


class MWidget:
    def __init__(self, x=0, y=0, w=0, h=0, parent=None):
        self.x, self.y, self.w, self.h = x, y, w, h
        self.parent = parent
        self.children = []
        self._visible = True
        self._pressed = False      # 新增：记录是否被按下
        self._press_in = False     # 新增：记录是否在本控件内按下
        if parent:
            parent.add_child(self)
    def add_child(self, child):
        child.parent = self
        self.children.append(child)
    def setVisible(self, visible: bool):
        if self._visible != visible:
            self._visible = visible
            mark_dirty()
    def isVisible(self):
        return self._visible
    def draw(self, img):
        if not self._visible:
            return
        self.paintEvent(img)
        for c in self.children:
            c.draw(img)
    def paintEvent(self, img):
        pass
    def hit_test(self, x, y, pressed=None):
        if not self._visible:
            return None
        # 先检查子控件（从上到下，后添加的在上层）
        for c in reversed(self.children):
            hit = c.hit_test(x, y, pressed)
            if hit:
                return hit
        # 检查自己
        if self.x <= x < self.x + self.w and self.y <= y < self.y + self.h:
            if pressed is not None:
                if pressed and not self._pressed:
                    self._pressed = True
                    self._press_in = True
                elif not pressed and self._pressed:
                    self._pressed = False
                    if self._press_in:
                        self._press_in = False
                        return self  # 只有按下后松开才返回自己
                return None
            else:
                return self
        else:
            if not pressed:
                self._press_in = False
                self._pressed = False
        return None