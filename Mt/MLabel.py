from maix import image
from Mt.MWidget import MWidget, mark_dirty

class MLabel(MWidget):
    # 文字缩放上限：普通标签不放大（1.0），数字键盘显示区等大标签可设为 2.0
    text_scale_max = 1.0
    # 文字缩放下限：再小就不可读了
    text_scale_min = 0.4

    def __init__(self, text, x=0, y=0, w=None, h=None, color=None, parent=None, align="left"):
        if w is None or h is None:
            lines = str(text).splitlines() or [""]
            sizes = []
            for line in lines:
                try:
                    size = image.string_size(line)
                    sizes.append((size.width(), size.height()))
                except Exception:
                    sizes.append((len(line) * 8, 16))
            max_w = max((item[0] for item in sizes), default=0)
            total_h = sum((item[1] for item in sizes), 0)
            if len(sizes) > 1:
                total_h += (len(sizes) - 1) * 4
            w = w or (max_w + 4)
            h = h or (total_h + 4)
        super().__init__(x, y, w, h, parent)
        self._text = text
        self.color = color or image.Color.from_rgb(0, 0, 0)
        self.align = align   # "left" / "center" / "right"
        self._image = None   # 新增：用于保存要绘制的图片
        # 缩放结果缓存：源图片对象与目标尺寸都没变时直接复用，避免每帧 resize。
        # _scaled_src 强引用源图片，防止源图被释放后 id 复用造成误判。
        self._scaled_src = None
        self._scaled_img = None
        self._scaled_size = (0, 0)

    @staticmethod
    def _measure_text(text):
        try:
            size = image.string_size(text)
            return size.width(), size.height()
        except Exception:
            return len(text) * 8, 16

    @classmethod
    def _measure_text_block(cls, text):
        lines = str(text).splitlines() or [""]
        line_sizes = [cls._measure_text(line) for line in lines]
        width = max((item[0] for item in line_sizes), default=0)
        height = sum((item[1] for item in line_sizes), 0)
        if len(line_sizes) > 1:
            height += (len(line_sizes) - 1) * 4
        return width, height

    def setText(self, text):
        if self._text != text:
            self._text = text
            mark_dirty()

    def text(self):
        return self._text

    def _fit_scale(self):
        """文本块超出控件时按比例缩小；空间富余且 text_scale_max > 1 时允许放大。"""
        tw, th = self._measure_text_block(self._text)
        if tw <= 0 or th <= 0:
            return 1.0
        scale = min(self.w / (tw + 4), self.h / (th + 4), self.text_scale_max)
        return max(self.text_scale_min, scale)

    @staticmethod
    def _draw_string_scaled(img, x, y, text, color, scale):
        if abs(scale - 1.0) < 1e-3:
            img.draw_string(x, y, text, color)
            return
        try:
            img.draw_string(x, y, text, color, scale=scale)
        except TypeError:
            img.draw_string(x, y, text, color)

    def _calc_text_pos(self):
        """根据对齐方式计算文本绘制起点（含自适应缩放）。"""
        scale = self._fit_scale()
        tw, th = self._measure_text_block(self._text)
        tw, th = int(tw * scale), int(th * scale)

        if self.align == "center":
            x_offset = max(0, (self.w - tw) // 2)
            y_offset = max(0, (self.h - th) // 2)
        elif self.align == "right":
            x_offset = max(0, self.w - tw - 2)
            y_offset = max(0, (self.h - th) // 2)
        else:  # left
            x_offset = 2
            y_offset = max(0, (self.h - th) // 2) if self.h > th else 2
        return self.x + x_offset, self.y + y_offset, scale

    # 新增：设置要显示的图片（传入 maix.image.Image 对象）
    def setImage(self, img):
        # 先释放旧图引用，避免内存堆积
        self.clearImage()
        self._image = img
        mark_dirty()
        # 可选：如果标签未指定宽高，则自动根据图片大小调整
        if (self.w == 0 or self.h == 0) and hasattr(img, "width") and hasattr(img, "height"):
            try:
                iw = img.width()
                ih = img.height()
                if iw and ih:
                    self.w = iw
                    self.h = ih
            except Exception:
                pass

    def clearImage(self):
        self._image = None
        self._scaled_src = None
        self._scaled_img = None
        mark_dirty()

    def paintEvent(self, img):
        if not self.isVisible():
            return
        # 如果设置了图片，则绘制图片；否则绘制文本
        if self._image is not None:
            try:
                # 优先复用缓存的缩放结果：源图片对象没变且目标尺寸没变就不重新 resize
                if self._image is self._scaled_src and self._scaled_size == (self.w, self.h):
                    scaled = self._scaled_img
                else:
                    scaled = None
                    # 源图与控件同尺寸时无需缩放，直接绘制原图（相机全屏显示的常见路径，
                    # 避免每帧对 640x480 图像做一次无意义的 resize）
                    try:
                        if self._image.width() == self.w and self._image.height() == self.h:
                            scaled = self._image
                    except Exception:
                        scaled = None
                    if scaled is None:
                        # 优先尝试图片对象的 resize 方法
                        try:
                            if hasattr(self._image, "resize"):
                                scaled = self._image.resize(self.w, self.h)
                            # 其次尝试模块级的 resize 接口
                            elif hasattr(image, "resize"):
                                scaled = image.resize(self._image, self.w, self.h)
                            else:
                                scaled = self._image
                        except Exception:
                            scaled = self._image

                    if scaled is None:
                        scaled = self._image

                    # 只有真正产生了新的缩放图才缓存（兜底直接用原图时不缓存，
                    # 避免原图被强引用无法释放）
                    if scaled is not self._image:
                        self._scaled_src = self._image
                        self._scaled_img = scaled
                        self._scaled_size = (self.w, self.h)

                # 绘制缩放后的图片，兼容 draw_image / draw_picture
                try:
                    img.draw_image(self.x, self.y, scaled)
                except Exception:
                    try:
                        img.draw_picture(self.x, self.y, scaled)
                    except Exception:
                        # 最后兜底：直接不绘制图片，改为绘制文本以免抛错
                        tx, ty, scale = self._calc_text_pos()
                        self._draw_string_scaled(img, tx, ty, self._text, self.color, scale)
            except Exception:
                tx, ty, scale = self._calc_text_pos()
                self._draw_string_scaled(img, tx, ty, self._text, self.color, scale)
        else:
            lines = str(self._text).splitlines() or [""]
            scale = self._fit_scale()
            _, block_h = self._measure_text_block(self._text)
            block_h = int(block_h * scale)
            line_gap = max(1, int(4 * scale))
            start_y = self.y + max(0, (self.h - block_h) // 2)
            current_y = start_y
            for line in lines:
                line_w, line_h = self._measure_text(line)
                line_w, line_h = int(line_w * scale), int(line_h * scale)
                if self.align == "center":
                    line_x = self.x + max(0, (self.w - line_w) // 2)
                elif self.align == "right":
                    line_x = self.x + max(0, self.w - line_w - 2)
                else:
                    line_x = self.x + 2
                self._draw_string_scaled(img, line_x, current_y, line, self.color, scale)
                current_y += line_h + line_gap
        
    def hit_test(self, x, y, pressed=None):
        if not self.isVisible():
            return None
        if self.x <= x < self.x + self.w and self.y <= y < self.y + self.h:
            return self
        return None