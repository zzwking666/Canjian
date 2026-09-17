"""
数字键盘（NumberKeyBoard）布局仿真测试。

对三种语言分别校验：
- 所有子控件（显示区、数字键、OK/0/退格、取消）都在对话框范围内；
- OK / 取消按钮文本单行完整显示、不溢出（越南语/英文文本较宽）；
- 密码模式提示文本在显示区宽度内。
"""
import unittest

# ---------------- stub maix 模块（必须在导入 Mt/MaixCam 组件前完成） ----------------
import maix_stub

maix_stub.install()

# ---------------------------------------------------------------------------

from MaixCam.I18n import set_language, tr
from Mt.MPushButton import MPushButton
from Mt.NumberKeyBoard import NumberKeyBoard

# 与 MainWindow 中实际使用的尺寸一致
KB_X, KB_Y, KB_W, KB_H = 60, 10, 520, 460


class TestNumberKeyBoardLayout(unittest.TestCase):
    def _check(self, password):
        for lang in ("zh", "en", "vi"):
            with self.subTest(lang=lang, password=password):
                set_language(lang)
                kb = NumberKeyBoard(KB_X, KB_Y, KB_W, KB_H, max_len=8, password=password)
                right = kb.x + kb.w
                bottom = kb.y + kb.h
                for child in kb.children:
                    self.assertGreaterEqual(child.x, kb.x)
                    self.assertGreaterEqual(child.y, kb.y)
                    self.assertLessEqual(child.x + child.w, right,
                                         f"{lang}: 控件右缘超出对话框")
                    self.assertLessEqual(child.y + child.h, bottom,
                                         f"{lang}: 控件下缘超出对话框")
                    # 带文本的按钮：单行显示且文本块高度不超过按钮高度
                    if isinstance(child, MPushButton) and child.text():
                        lines = MPushButton.wrap_text(child.text(), child.w, padding=8)
                        self.assertEqual(len(lines), 1,
                                         f"{lang}: 按钮文本 {child.text()!r} 折行了")
                        text_h = MPushButton.text_block_height(child.text(), child.w, padding=8)
                        self.assertLessEqual(text_h, child.h,
                                             f"{lang}: 按钮文本 {child.text()!r} 溢出按钮")
                # 密码模式提示文本不超过显示区宽度
                if password:
                    text_w, text_h = kb.display_label._measure_text_block(
                        kb.display_label.text())
                    self.assertLessEqual(text_w, kb.display_label.w)
                    self.assertLessEqual(text_h, kb.display_label.h)

    def test_layout_password_mode(self):
        self._check(password=True)

    def test_layout_normal_mode(self):
        self._check(password=False)

    def tearDown(self):
        set_language("zh")


if __name__ == "__main__":
    unittest.main()
