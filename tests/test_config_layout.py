"""
配置页（产量参数/系统参数）布局仿真测试。

通过 stub maix 与硬件相关模块，在本机实例化 MaixCamMainWindow(640x480)，
对三种语言分别校验：
- 所有控件都在页面范围内；
- 每列参数内：参数名在上、数值按钮居中、单位在下，垂直方向不重叠；
- 各列之间水平方向不重叠；
- MPanel 装饰面板不拦截触摸事件。
"""
import sys
import types
import unittest

# ---------------- stub maix 模块（必须在导入 Mt/MaixCam 组件前完成） ----------------
# 统一使用共享 stub，避免与其它测试文件的 sys.modules.setdefault 互相覆盖
import maix_stub

maix_stub.install()

# ---------------- stub 硬件相关 MaixCam 模块 ----------------

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
        self.actionQueue = []

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

from MaixCam.I18n import set_language, tr
from MaixCam.MainWindow import MaixCamMainWindow
from Mt.MPanel import MPanel
from Mt.MPushButton import MPushButton

SCREEN_W, SCREEN_H = 640, 480


def _rect(w):
    return (w.x, w.y, w.x + w.w, w.y + w.h)


def _overlap(a, b):
    ax0, ay0, ax1, ay1 = _rect(a)
    bx0, by0, bx1, by1 = _rect(b)
    return ax0 < bx1 and bx0 < ax1 and ay0 < by1 and by0 < ay1


class TestConfigPageLayout(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.win = MaixCamMainWindow(0, 0, SCREEN_W, SCREEN_H, margin=0)

    def _check_page(self, container, rows, exit_btn, title):
        # 标题与退出按钮均在页面范围内，且互不重叠
        for w in (title, exit_btn):
            self.assertGreaterEqual(w.x, 0)
            self.assertGreaterEqual(w.y, 0)
            self.assertLessEqual(w.x + w.w, container.w)
            self.assertLessEqual(w.y + w.h, container.h)
        self.assertFalse(_overlap(title, exit_btn))

        prev_right = 0
        for label, btn, unit in rows:
            # 控件均在页面范围内
            for w in (label, btn, unit):
                self.assertGreaterEqual(w.x, 0)
                self.assertGreaterEqual(w.y, 0)
                self.assertLessEqual(w.x + w.w, container.w)
                self.assertLessEqual(w.y + w.h, container.h)
            # 列与上一列水平方向不重叠（左->右排列）
            self.assertGreaterEqual(label.x, prev_right)
            prev_right = label.x + label.w
            # 列内 上->下：参数名 -> 数值按钮 -> 单位，互不重叠
            self.assertLessEqual(label.y + label.h, btn.y)
            self.assertLessEqual(btn.y + btn.h, unit.y)
            # 参数名/单位标签位于同一列内且与按钮水平居中对齐
            self.assertEqual(label.x, unit.x)
            self.assertEqual(label.w, unit.w)
            # 标签文本经自适应缩小后能放进标签区域
            for lb in (label, unit):
                text_w, text_h = lb._measure_text_block(lb.text())
                scale = max(lb.text_scale_min,
                            min(lb.w / (text_w + 4), lb.h / (text_h + 4), 1.0))
                self.assertLessEqual(int(text_w * scale), lb.w)
                self.assertLessEqual(int(text_h * scale), lb.h)

    def _prod_rows(self):
        w = self.win
        return [
            (w.lb_dadouyici, w.btn_dadouyici, w.lb_dadouyiciUnit),
            (w.lb_xiaodouyici, w.btn_xiaodouyici, w.lb_xiaodouyiciUnit),
            (w.lb_zongshu, w.btn_zongshu, w.lb_zongshuUnit),
            (w.lb_wusuijian, w.btn_wusuijian, w.lb_wusuijianUnit),
        ]

    def _sys_rows(self):
        w = self.win
        return [
            (w.lb_jiange, w.btn_jiange, w.lb_jiangeUnit),
            (w.lb_chufashijian, w.btn_chufashijian, w.lb_chufashijianUnit),
            (w.lb_yanshichufashijian, w.btn_yanshichufashijian, w.lb_yanshichufashijianUnit),
        ]

    def test_layout_all_languages(self):
        for lang in ("zh", "en", "vi"):
            with self.subTest(lang=lang):
                set_language(lang)
                self.win._update_ui_texts()
                self._check_page(
                    self.win.configProdContainer, self._prod_rows(),
                    self.win.exit_config_prod_btn, self.win.title_config_prod)
                self._check_page(
                    self.win.configSysContainer, self._sys_rows(),
                    self.win.exit_config_sys_btn, self.win.title_config_sys)

    def test_language_button_not_overlapping_rows(self):
        for lang in ("zh", "en", "vi"):
            with self.subTest(lang=lang):
                set_language(lang)
                self.win._update_ui_texts()
                for label, btn, unit in self._prod_rows():
                    self.assertFalse(_overlap(self.win.btn_language, btn))
                    self.assertFalse(_overlap(self.win.btn_language, unit))

    def test_language_button_text_fits_all_languages(self):
        """语言按钮尺寸固定：三种语言名都必须单行完整显示，不溢出、不超界。"""
        for lang in ("zh", "en", "vi"):
            with self.subTest(lang=lang):
                set_language(lang)
                self.win._update_ui_texts()
                btn = self.win.btn_language
                # 按钮在页面范围内
                self.assertGreaterEqual(btn.x, 0)
                self.assertGreaterEqual(btn.y, 0)
                self.assertLessEqual(btn.x + btn.w, self.win.configProdContainer.w)
                self.assertLessEqual(btn.y + btn.h, self.win.configProdContainer.h)
                # 语言名不换行（单行显示），且文本块高度不超过按钮高度
                lines = MPushButton.wrap_text(btn.text(), btn.w, padding=8)
                self.assertEqual(len(lines), 1,
                                 f"{lang}: 语言名 {btn.text()!r} 在 {btn.w}px 宽按钮内折行了")
                text_h = MPushButton.text_block_height(btn.text(), btn.w, padding=8)
                self.assertLessEqual(text_h, btn.h)

    def test_header_exit_button_fits_all_languages(self):
        """各页退出按钮尺寸固定：三语"退出"文本都必须单行完整显示，不溢出、不超界。"""
        w = self.win
        cases = [
            (w.exit_config_prod_btn, w.configProdContainer),
            (w.exit_config_sys_btn, w.configSysContainer),
            (w.exit_debug_btn, w.debugContainer),
            (w.exit_release_btn, w.releaseContainer),
        ]
        for lang in ("zh", "en", "vi"):
            with self.subTest(lang=lang):
                set_language(lang)
                w._update_ui_texts()
                for btn, container in cases:
                    # 按钮在页面范围内
                    self.assertGreaterEqual(btn.x, 0)
                    self.assertGreaterEqual(btn.y, 0)
                    self.assertLessEqual(btn.x + btn.w, container.w)
                    self.assertLessEqual(btn.y + btn.h, container.h)
                    # 单行显示且文本块高度不超过按钮高度
                    lines = MPushButton.wrap_text(btn.text(), btn.w, padding=8)
                    self.assertEqual(len(lines), 1,
                                     f"{lang}: 退出文本 {btn.text()!r} 在 {btn.w}px 宽按钮内折行了")
                    text_h = MPushButton.text_block_height(btn.text(), btn.w, padding=8)
                    self.assertLessEqual(text_h, btn.h)

    def test_menu_layout_all_languages(self):
        """菜单页：标题 + 四按钮，三语下均在页面内、不重叠、文本不溢出。"""
        w = self.win
        btns = [w.btn_debug, w.btn_release, w.btn_config_prod, w.btn_config_sys]
        for lang in ("zh", "en", "vi"):
            with self.subTest(lang=lang):
                set_language(lang)
                w._update_ui_texts()
                # 标题文本单行不溢出
                _, title_h = w.titleLabel._measure_text_block(w.titleLabel.text())
                self.assertLessEqual(title_h, w.titleLabel.h)
                prev_bottom = w.titleLabel.y + w.titleLabel.h
                for btn in btns:
                    # 按钮在页面范围内、在标题之下、与上一按钮不重叠
                    self.assertGreaterEqual(btn.x, 0)
                    self.assertGreaterEqual(btn.y, prev_bottom)
                    self.assertLessEqual(btn.x + btn.w, w.menuContainer.w)
                    self.assertLessEqual(btn.y + btn.h, w.menuContainer.h)
                    prev_bottom = btn.y + btn.h
                    # 文本折行后不溢出按钮
                    text_h = MPushButton.text_block_height(btn.text(), btn.w, padding=8)
                    self.assertLessEqual(text_h, btn.h,
                                         f"{lang}: 菜单按钮文本 {btn.text()!r} 溢出按钮")

    def test_release_layout_all_languages(self):
        """运行页布局：三种语言下所有控件在页面内、文本不溢出、按钮互不重叠。

        相机画面为全屏底图，控件叠加在上层（重叠属设计行为，不在此断言）。
        """
        w = self.win
        col_btns = [w.exit_release_btn, w.countButtonRun, w.douStatus,
                    w.triggerCircleLabel_ms, w.btn_shutdown]
        for lang in ("zh", "en", "vi"):
            with self.subTest(lang=lang):
                set_language(lang)
                w._update_ui_texts()
                # 所有控件在页面范围内
                for btn in col_btns + [w.actuatorStatus, w.gpioStatus,
                                       w.sysInfoLabel, w.logoLabel]:
                    self.assertGreaterEqual(btn.x, 0)
                    self.assertGreaterEqual(btn.y, 0)
                    self.assertLessEqual(btn.x + btn.w, w.releaseContainer.w)
                    self.assertLessEqual(btn.y + btn.h, w.releaseContainer.h)
                # 带文本的按钮：按实际绘制逻辑（排版+自适应缩放）后文本块不溢出按钮
                for btn in (w.exit_release_btn, w.douStatus,
                            w.btn_shutdown, w.actuatorStatus):
                    _, line_height = btn.measure_text("Ag")
                    line_height = max(16, line_height)
                    lines, scale = btn._layout_lines(line_height)
                    scaled_h = int(line_height * scale) * len(lines) \
                        + max(1, int(4 * scale)) * max(0, len(lines) - 1)
                    self.assertLessEqual(scaled_h, btn.h,
                                         f"{lang}: {btn.text()!r} 缩放后仍溢出按钮")
                # 右列按钮之间不重叠，且不与执行状态按钮重叠
                prev = None
                for btn in col_btns:
                    if prev is not None:
                        self.assertFalse(_overlap(prev, btn))
                    self.assertFalse(_overlap(btn, w.actuatorStatus))
                    prev = btn
                self.assertFalse(_overlap(w.gpioStatus, w.actuatorStatus))
                # logo 位于右上角按钮列上方，不与按钮列重叠
                for btn in col_btns:
                    self.assertFalse(_overlap(w.logoLabel, btn),
                                     f"{lang}: logo 与按钮列重叠")
                self.assertLessEqual(w.logoLabel.y + w.logoLabel.h, w.exit_release_btn.y)
                # 相机画面铺满整个页面（全屏底图）
                self.assertEqual(w.labelDisImgRel.w, w.releaseContainer.w)
                self.assertEqual(w.labelDisImgRel.h, w.releaseContainer.h)

    def test_value_buttons_styled_as_clickable(self):
        # 数值按钮应为白底蓝框，与普通灰色按钮区分
        for _, btn, _ in self._prod_rows() + self._sys_rows():
            self.assertEqual(btn.bg_color, (255, 255, 255))
            self.assertEqual(btn.border_color, (100, 149, 237))

    def test_menu_highlight_follows_last_visited(self):
        """菜单高亮：从哪个界面退出回菜单，对应按钮绿色突出，其余恢复浅蓝灰。"""
        from unittest import mock
        w = self.win
        GREEN = (76, 175, 80)
        NORMAL = (227, 242, 253)
        all_btns = [w.btn_debug, w.btn_release, w.btn_config_prod, w.btn_config_sys]
        cases = [
            (w.on_debug_clicked, w.btn_debug),
            (w.on_config_prod_clicked, w.btn_config_prod),
            (w.on_release_clicked, w.btn_release),
        ]
        # 屏蔽退出时的配置写盘副作用（仿真环境无真实路径）
        with mock.patch.object(_FakeModules.instance().config, "save", return_value=True):
            # 初始（默认运行模式启动）：运行模式按钮绿色
            self.assertEqual(w.btn_release.bg_color, GREEN)
            for enter, active in cases:
                with self.subTest(active=active.text()):
                    enter()
                    w.on_exit_to_menu()
                    self.assertEqual(w.tabWidget.currentIndex(), w.TAB_MENU)
                    for b in all_btns:
                        self.assertEqual(b.bg_color, GREEN if b is active else NORMAL)

    def test_panel_does_not_intercept_touch(self):
        panel = MPanel(0, 0, 100, 100)
        self.assertIsNone(panel.hit_test(50, 50, pressed=True))
        self.assertIsNone(panel.hit_test(50, 50, pressed=False))
        self.assertIsNone(panel.hit_test(50, 50))

    def tearDown(self):
        set_language("zh")


if __name__ == "__main__":
    unittest.main()
