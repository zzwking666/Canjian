from Mt.MMainWindow import MMainWindow
from Mt.MTabWidget import MTabWidget,MTabPage
from Mt.MLabel import MLabel
from Mt.MPushButton import MPushButton
from Mt.MLongPressButton import MLongPressButton
from Mt.MWidget import MWidget
from Mt.MDialog import MDialog
from Mt.MApplication import MApplication
from MaixCam.RunningInfo import RunningInfo, RunMode,DouMode
from MaixCam.Modules import Modules
from Mt.NumberKeyBoard import NumberKeyBoard
from MaixCam.TaskGPIOManager import TaskGPIOManager
from MaixCam.Action import setDaDouStatus,setXiaoDouStatus
from MaixCam.I18n import set_language, tr, current_language

from maix import image

class MaixCamMainWindow(MMainWindow):
    # tab 页面索引常量
    TAB_MENU = 0
    TAB_DEBUG = 1
    TAB_RELEASE = 2
    TAB_CONFIG_PROD = 3
    TAB_CONFIG_SYS = 4
    # 系统参数页进入密码（防误操作级别，硬编码）
    SYSTEM_PARAMS_PASSWORD = "8888"

    def __init__(self, x, y, width, height, margin=0):
        super().__init__(x, y, width, height)
        self.width = width
        self.height = height
        self.margin = margin

        # 根据配置文件设置当前语言
        set_language(Modules.instance().config.language)

        self.buildUI()

        # the img display label for debug
        Modules.instance().disDebug=self.labelDisImgDebug
        # the img display label for release
        Modules.instance().disRelease=self.labelDisImgRel
        # the canjian counts display buttons for debug
        Modules.instance().countLabel=self.countButton
        # the canjian counts display buttons for release
        Modules.instance().countLabelRun=self.countButtonRun
        # the dou status display button for release (based on recognized count)
        Modules.instance().douStatus=self.douStatus
        # the actuator status display button for release (based on IO execution)
        Modules.instance().actuatorStatus=self.actuatorStatus
        # the GPIO input signal status indicator for release
        Modules.instance().gpioStatus=self.gpioStatus
        # the trigger circle label for release
        Modules.instance().triggerCircleLabel_ms=self.triggerCircleLabel_ms

        # Test for default start in Debug mode
        self.tabWidget.setCurrentIndex(self.TAB_RELEASE)
        RunningInfo.instance().run_mode = RunMode.RUN
        TaskGPIOManager.instance().startTaskManager()

    def buildUI(self):
        self.tabWidget = MTabWidget(self.margin, self.margin, self.width - self.margin*2, self.height -  self.margin*2)
        self.tabWidget.setTabBarVisible(False)

        self.build_Menu()
        self.build_Debug()
        self.build_Release()
        self.build_ConfigProd()
        self.build_ConfigSys()

        self.addWidget(self.tabWidget)

    def build_Menu(self):
        # 创建一个页面容器
        self.menuContainer = MTabPage(0, 0, self.tabWidget.w, self.tabWidget.h)

        # 创建Title并居中
        self.titleLabel = MLabel(text=tr("select_mode"), x=0, y=0)
        self.titleLabel.x = (self.menuContainer.w - self.titleLabel.w) // 2
        self.titleLabel.y = self.margin + 5

        # 按钮参数（加大尺寸便于触屏，英/越语文本由 MPushButton 自动缩放适配）
        # 按钮区从标题下方开始
        btn_count = 4
        btn_width = int(self.menuContainer.w * 0.62)
        btn_height = max(64, int(self.menuContainer.h * 0.15))
        btn_area_top = self.titleLabel.y + self.titleLabel.h + 8
        btn_gap = max(8, int((self.menuContainer.h - btn_area_top - btn_count * btn_height) / (btn_count + 1)))
        btn_x = (self.menuContainer.w - btn_width) // 2
        btn_y_start = btn_area_top + btn_gap

        # 分别创建并命名按钮（竖直排列），最后进入过的界面按钮绿色突出，其余浅蓝灰
        self.btn_debug = MPushButton(text=tr("debug_mode"), x=btn_x, y=btn_y_start, w=btn_width, h=btn_height)
        self.btn_release = MPushButton(text=tr("run_mode"), x=btn_x, y=btn_y_start + btn_height + btn_gap, w=btn_width, h=btn_height)
        self.btn_config_prod = MPushButton(text=tr("production_params"), x=btn_x, y=btn_y_start + (btn_height + btn_gap) * 2, w=btn_width, h=btn_height)
        self.btn_config_sys = MPushButton(text=tr("system_params"), x=btn_x, y=btn_y_start + (btn_height + btn_gap) * 3, w=btn_width, h=btn_height)

        self._menu_btns = (self.btn_debug, self.btn_release, self.btn_config_prod, self.btn_config_sys)
        # 默认从运行模式启动，运行模式按钮初始为绿色
        self._last_menu_btn = self.btn_release
        self._highlight_menu_button(self._last_menu_btn)

        # 连接槽函数
        self.btn_debug.clicked.connect(self.on_debug_clicked)
        self.btn_release.clicked.connect(self.on_release_clicked)
        self.btn_config_prod.clicked.connect(self.on_config_prod_clicked)
        self.btn_config_sys.clicked.connect(self.on_config_sys_clicked)

        self.menuContainer.add_child(self.titleLabel)
        self.menuContainer.add_child(self.btn_debug)
        self.menuContainer.add_child(self.btn_release)
        self.menuContainer.add_child(self.btn_config_prod)
        self.menuContainer.add_child(self.btn_config_sys)

        # 添加到tab
        self.tabWidget.addTab(self.menuContainer, tr("menu"))

    def _highlight_menu_button(self, active_btn):
        """菜单按钮配色：active_btn 绿色突出，其余浅蓝灰。"""
        for b in self._menu_btns:
            if b is active_btn:
                b.bg_color = image.Color.from_rgb(76, 175, 80)
                b.text_color = image.Color.from_rgb(255, 255, 255)
                b.border_color = image.Color.from_rgb(56, 142, 60)
            else:
                b.bg_color = image.Color.from_rgb(227, 242, 253)
                b.text_color = image.Color.from_rgb(0, 0, 0)
                b.border_color = image.Color.from_rgb(100, 149, 237)
    def on_shutdown_clicked(self):
        print(tr("shutdown_clicked"))
        # 弹出正在关机提示框（非模态），按实际画布尺寸居中，停留 1 秒后自动关机
        app = MApplication.instance()
        dlg_w, dlg_h = 540, 180
        dlg_x = max(0, (app.img_width - dlg_w) // 2)
        dlg_y = max(0, (app.img_height - dlg_h) // 2)
        dialog = MDialog(dlg_x, dlg_y, dlg_w, dlg_h)
        label = MLabel(text=tr("shutting_down"), x=dialog.x + 20, y=dialog.y + (dlg_h - 60) // 2, w=dialog.w - 40, h=60, align="center")
        dialog.addWidget(label)
        dialog.show()
        # 刷新界面 1 秒，让用户看到提示
        for _ in range(100):  # 100 * 10ms = 1s
            try:
                app._process_event_and_repaint(dialog=dialog, interval_ms=10)
            except Exception:
                break
        # 执行关机：先同步文件系统，避免缓存数据未落盘导致损坏
        import os
        try:
            os.sync()
        except Exception:
            pass
        os.system("poweroff")

    def build_Debug(self):
        self.debugContainer = MTabPage(0, 0, self.tabWidget.w, self.tabWidget.h)

        # 相机画面全屏显示（先添加，退出/计数按钮叠加在上层）
        self.labelDisImgDebug= MLabel(text=tr("debug_image"), x=0, y=0, w=self.debugContainer.w, h=self.debugContainer.h)
        self.debugContainer.add_child(self.labelDisImgDebug)

        btn_w = 100
        btn_h = 50
        btn_margin = 10
        btn_x = self.debugContainer.w - btn_w - btn_margin  # 右上角
        btn_y = btn_margin
        self.exit_debug_btn = MPushButton(text=tr("exit"), x=btn_x, y=btn_y, w=btn_w, h=btn_h)
        self.exit_debug_btn.clicked.connect(self.on_exit_to_menu)
        self.debugContainer.add_child(self.exit_debug_btn)

        btn_y += 70
        self.countButton=MPushButton(text=tr("count_prefix") + "0",x=btn_x, y=btn_y, w=btn_w, h=btn_h)
        self.debugContainer.add_child(self.countButton)

        self.tabWidget.addTab(self.debugContainer, tr("debug_mode"))

    def build_Release(self):
        self.releaseContainer = MTabPage(0, 0, self.tabWidget.w, self.tabWidget.h)

        btn_w = 100
        btn_h = 50
        btn_margin = 10
        btn_step = 64   # 按钮列垂直步距

        # 执行机构状态按钮尺寸（按最长文本自适应）
        actuator_texts = [
            tr("actuator_big_dou"),
            tr("actuator_small_dou"),
            tr("actuator_both_dou"),
            tr("actuator_stop"),
        ]
        try:
            actuator_max_w = max(image.string_size(t).width() for t in actuator_texts)
            actuator_btn_w = actuator_max_w + 16
            actuator_btn_h = max(
                MPushButton.text_block_height(text, actuator_btn_w, padding=8)
                for text in actuator_texts
            )
        except Exception:
            actuator_btn_w = btn_w
            actuator_btn_h = btn_h

        # 左下角 GPIO 输入信号指示灯位置
        gpio_indicator_size = 40
        gpio_btn_x = btn_margin
        gpio_btn_y = self.releaseContainer.h - gpio_indicator_size - btn_margin

        # 执行机构状态位置：GPIO 指示灯右侧，底部对齐
        actuator_btn_x = gpio_btn_x + gpio_indicator_size + btn_margin
        actuator_btn_y = self.releaseContainer.h - actuator_btn_h - btn_margin

        # 相机画面全屏显示（先添加，按钮/状态控件叠加在上层）
        self.labelDisImgRel = MLabel(text=tr("running"), x=0, y=0, w=self.releaseContainer.w, h=self.releaseContainer.h)
        self.releaseContainer.add_child(self.labelDisImgRel)

        # 右上角 logo 图标：宽 200、高 110，右对齐位于按钮列上方；
        # 文件缺失或加载失败时隐藏（其占位区域保留，按钮列位置固定不变）
        btn_x = self.releaseContainer.w - btn_w - btn_margin
        logo_w = btn_w * 2
        logo_h = 110
        logo_x = btn_x + btn_w - logo_w
        self.logoLabel = MLabel(
            text="",
            x=logo_x,
            y=btn_margin,
            w=logo_w, h=logo_h
        )
        self.logoLabel.setVisible(False)
        self.releaseContainer.add_child(self.logoLabel)
        try:
            logo_img = image.load(Modules.instance().paths.logo_path)
            self.logoLabel.setImage(logo_img)
            self.logoLabel.setVisible(True)
        except Exception as e:
            print("logo 加载失败，已隐藏:", e)

        # 右侧按钮列：从 logo 占位区下方起排（列底距屏幕底边恰好一个边距）
        btn_gap = btn_step - btn_h
        shutdown_h = btn_h + 30
        col_h = 4 * btn_h + shutdown_h + 4 * btn_gap
        btn_y = btn_margin + logo_h + btn_gap
        btn_y = max(btn_margin, min(btn_y, self.releaseContainer.h - btn_margin - col_h))
        self.exit_release_btn = MPushButton(text=tr("exit"), x=btn_x, y=btn_y, w=btn_w, h=btn_h)
        self.exit_release_btn.clicked.connect(self.on_exit_to_menu)
        self.releaseContainer.add_child(self.exit_release_btn)

        btn_y += btn_step
        self.countButtonRun = MPushButton(text="0", x=btn_x, y=btn_y, w=btn_w, h=btn_h)
        self.releaseContainer.add_child(self.countButtonRun)

        btn_y += btn_step
        self.douStatus = MPushButton(text=tr("status_stop"), x=btn_x, y=btn_y, w=btn_w, h=btn_h)
        self.releaseContainer.add_child(self.douStatus)

        btn_y += btn_step
        self.triggerCircleLabel_ms = MPushButton(text="0ms", x=btn_x, y=btn_y, w=btn_w, h=btn_h)
        self.releaseContainer.add_child(self.triggerCircleLabel_ms)

        # 新增关机按钮（长按 1 秒才触发关机），红色警示配色
        btn_y += btn_step
        self.btn_shutdown = MLongPressButton(text=tr("shutdown"), x=btn_x, y=btn_y, w=btn_w, h=btn_h+30, long_press_ms=1000)
        # 英文 "Power\nOff" 两行显示时字号缩小一号，其他语言保持原大小
        self.btn_shutdown.text_scale_max = 0.8 if current_language() == "en" else 1.0
        self.btn_shutdown.bg_color = image.Color.from_rgb(229, 115, 115)
        self.btn_shutdown.text_color = image.Color.from_rgb(255, 255, 255)
        self.btn_shutdown.border_color = image.Color.from_rgb(198, 80, 80)
        self.btn_shutdown._normal_bg_color = self.btn_shutdown.bg_color
        self.btn_shutdown._pressing_bg_color = image.Color.from_rgb(183, 74, 74)
        self.btn_shutdown.long_pressed.connect(self.on_shutdown_clicked)
        self.releaseContainer.add_child(self.btn_shutdown)

        # 左下角 GPIO 指示灯右侧：执行机构大小斗状态
        self.actuatorStatus = MPushButton(
            text=tr("actuator_stop"),
            x=actuator_btn_x, y=actuator_btn_y,
            w=actuator_btn_w, h=actuator_btn_h
        )
        self.releaseContainer.add_child(self.actuatorStatus)

        # 左下角：GPIO 输入信号状态指示灯（低电平=绿色，高电平=红色）
        self.gpioStatus = MPushButton(
            text="",
            x=gpio_btn_x, y=gpio_btn_y,
            w=gpio_indicator_size, h=gpio_indicator_size
        )
        self.gpioStatus.bg_color = image.Color.from_rgb(220, 80, 80)
        self.gpioStatus.border_color = image.Color.from_rgb(120, 120, 120)
        self.releaseContainer.add_child(self.gpioStatus)

        # 底部状态条中间空余区域：资源监控角标（整机 CPU/内存 + 本进程 CPU/RSS），
        # 字号由 MLabel 自适应缩小，每 3s 与心跳重绘同步刷新
        sysinfo_x = actuator_btn_x + actuator_btn_w + btn_margin
        sysinfo_w = btn_x - sysinfo_x - btn_margin
        sysinfo_h = max(gpio_indicator_size, actuator_btn_h)
        self.sysInfoLabel = MLabel(
            text="", x=sysinfo_x,
            y=self.releaseContainer.h - sysinfo_h - btn_margin,
            w=sysinfo_w, h=sysinfo_h,
            color=image.Color.from_rgb(90, 90, 90), align="left"
        )
        self.releaseContainer.add_child(self.sysInfoLabel)
        Modules.instance().sysInfoLabel = self.sysInfoLabel

        self.tabWidget.addTab(self.releaseContainer, tr("run_mode"))

    @staticmethod
    def _style_value_button(btn):
        """配置页数值按钮统一样式：白底蓝边，类似输入框，数字适当放大。"""
        btn.bg_color = image.Color.from_rgb(255, 255, 255)
        btn.border_color = image.Color.from_rgb(100, 149, 237)
        btn.text_color = image.Color.from_rgb(33, 33, 33)
        btn.text_scale_max = 1.6

    def _add_config_col(self, container, col_x, col_y, col_w, label_text, value_text, unit_text, on_click,
                        label_h=48, btn_h=76, btn_w_max=160):
        """配置页参数列：标签在上（居中），数值按钮居中，单位在按钮下方（居中）。"""
        lb = MLabel(text=label_text, x=col_x, y=col_y, w=col_w, h=label_h, align="center")
        container.add_child(lb)
        btn_w = min(col_w - 10, btn_w_max)
        btn = MPushButton(text=value_text, x=col_x + (col_w - btn_w) // 2, y=col_y + label_h + 8,
                          w=btn_w, h=btn_h)
        self._style_value_button(btn)
        btn.clicked.connect(on_click)
        container.add_child(btn)
        lb_unit = MLabel(text=unit_text, x=col_x, y=col_y + label_h + 8 + btn_h + 6,
                         w=col_w, h=30, align="center")
        container.add_child(lb_unit)
        return lb, btn, lb_unit

    @staticmethod
    def _col_positions(container_w, col_count, col_w, margin_x=20):
        """计算 col_count 列等宽等距排列的 x 坐标。"""
        gap = (container_w - 2 * margin_x - col_count * col_w) // max(1, col_count - 1) if col_count > 1 else 0
        gap = max(8, gap)
        total = col_count * col_w + (col_count - 1) * gap
        start_x = (container_w - total) // 2
        return [start_x + i * (col_w + gap) for i in range(col_count)]

    def _add_config_title(self, container, title_key):
        """配置页顶部居中标题，深蓝色。"""
        title = MLabel(text=tr(title_key), x=0, y=0)
        title.x = (container.w - title.w) // 2
        title.y = 18
        title.color = image.Color.from_rgb(25, 118, 210)
        container.add_child(title)
        return title

    def build_ConfigProd(self):
        """产量参数页：大斗一次/小斗一次/总数/无绪茧分割线 + 语言切换，无需密码直接进入。"""
        self.configProdContainer = MTabPage(0, 0, self.tabWidget.w, self.tabWidget.h)
        btn_margin = 10

        # 顶部标题
        self.title_config_prod = self._add_config_title(self.configProdContainer, "production_params")

        # 右上角退出按钮
        btn_w = 100
        btn_h = 50
        self.exit_config_prod_btn = MPushButton(
            text=tr("exit"),
            x=self.configProdContainer.w - btn_w - btn_margin, y=btn_margin,
            w=btn_w, h=btn_h
        )
        self.exit_config_prod_btn.clicked.connect(self.on_exit_to_menu)
        self.configProdContainer.add_child(self.exit_config_prod_btn)

        cfg = Modules.instance().config

        # 四个产量参数横向排列，每种参数一列（标签在上、数值按钮居中、单位在下）
        col_w = 135
        col_y = 110
        col_xs = self._col_positions(self.configProdContainer.w, 4, col_w)
        self.lb_dadouyici, self.btn_dadouyici, self.lb_dadouyiciUnit = self._add_config_col(
            self.configProdContainer, col_xs[0], col_y, col_w,
            tr("big_dou"), str(cfg.dadouyici), tr("unit_pcs"), self.on_dadouyici_clicked,
            btn_h=84, btn_w_max=125)
        self.lb_xiaodouyici, self.btn_xiaodouyici, self.lb_xiaodouyiciUnit = self._add_config_col(
            self.configProdContainer, col_xs[1], col_y, col_w,
            tr("small_dou"), str(cfg.xiaodouyici), tr("unit_pcs"), self.on_xiaodouyici_clicked,
            btn_h=84, btn_w_max=125)
        self.lb_zongshu, self.btn_zongshu, self.lb_zongshuUnit = self._add_config_col(
            self.configProdContainer, col_xs[2], col_y, col_w,
            tr("total"), str(cfg.zongshu), tr("unit_pcs"), self.on_zongshu_clicked,
            btn_h=84, btn_w_max=125)
        self.lb_wusuijian, self.btn_wusuijian, self.lb_wusuijianUnit = self._add_config_col(
            self.configProdContainer, col_xs[3], col_y, col_w,
            tr("disorder_percent"), str(cfg.wusuijian_fengexian), tr("unit_percent"), self.on_wusuijian_clicked,
            btn_h=84, btn_w_max=125)

        # 右下角语言切换按钮，大小按下一个语言名称文本尺寸自适应
        lang_text = tr("language_btn_en") if cfg.language == "zh" else tr("language_btn_vi") if cfg.language == "en" else tr("language_btn_zh")
        try:
            lang_size = image.string_size(lang_text)
            lang_btn_w = lang_size.width() + 24
            lang_btn_h = lang_size.height() + 24
        except Exception:
            lang_btn_w = btn_w
            lang_btn_h = btn_h
        lang_btn_x = self.configProdContainer.w - lang_btn_w - btn_margin
        lang_btn_y = self.configProdContainer.h - lang_btn_h - btn_margin
        self.btn_language = MPushButton(
            text=lang_text,
            x=lang_btn_x, y=lang_btn_y, w=lang_btn_w, h=lang_btn_h
        )
        self.btn_language.bg_color = image.Color.from_rgb(227, 242, 253)
        self.btn_language.border_color = image.Color.from_rgb(100, 149, 237)
        self.btn_language.clicked.connect(self.on_language_clicked)
        self.configProdContainer.add_child(self.btn_language)

        self.tabWidget.addTab(self.configProdContainer, tr("production_params"))

    def build_ConfigSys(self):
        """系统参数页：间隔/触发时间/延时触发，需密码进入。"""
        self.configSysContainer = MTabPage(0, 0, self.tabWidget.w, self.tabWidget.h)
        btn_margin = 10

        # 顶部标题
        self.title_config_sys = self._add_config_title(self.configSysContainer, "system_params")

        # 右上角退出按钮
        btn_w = 100
        btn_h = 50
        self.exit_config_sys_btn = MPushButton(
            text=tr("exit"),
            x=self.configSysContainer.w - btn_w - btn_margin, y=btn_margin,
            w=btn_w, h=btn_h
        )
        self.exit_config_sys_btn.clicked.connect(self.on_exit_to_menu)
        self.configSysContainer.add_child(self.exit_config_sys_btn)

        cfg = Modules.instance().config

        # 三个系统参数横向排列，每种参数一列（标签在上、数值按钮居中、单位在下）
        col_w = 180
        col_y = 150
        col_xs = self._col_positions(self.configSysContainer.w, 3, col_w)
        self.lb_jiange, self.btn_jiange, self.lb_jiangeUnit = self._add_config_col(
            self.configSysContainer, col_xs[0], col_y, col_w,
            tr("interval"), str(cfg.jiange), tr("unit_pcs"), self.on_jiange_clicked,
            btn_h=76)
        self.lb_chufashijian, self.btn_chufashijian, self.lb_chufashijianUnit = self._add_config_col(
            self.configSysContainer, col_xs[1], col_y, col_w,
            tr("trigger_percent"), str(cfg.chufashijian), tr("unit_percent"), self.on_chufashijian_clicked,
            btn_h=76)
        self.lb_yanshichufashijian, self.btn_yanshichufashijian, self.lb_yanshichufashijianUnit = self._add_config_col(
            self.configSysContainer, col_xs[2], col_y, col_w,
            tr("delay_percent"), str(cfg.yanshichufashijian), tr("unit_percent"), self.on_yanshichufashijian_clicked,
            btn_h=76)

        # 大斗/小斗 IO 手动控制按钮：按一下置 True，再按一下置 False；
        # True 时按钮绿色，False 时按钮红色（状态以 GPIO 实际电平为准）
        io_btn_w = 200
        io_btn_h = 60
        io_btn_y = col_y + 48 + 8 + 76 + 6 + 30 + 24  # 三列参数（标签+按钮+单位）下方
        io_col_xs = self._col_positions(self.configSysContainer.w, 2, io_btn_w)
        self.btn_dadou_io = MPushButton(
            text=tr("big_dou_io"),
            x=io_col_xs[0], y=io_btn_y, w=io_btn_w, h=io_btn_h
        )
        self.btn_dadou_io.clicked.connect(self.on_dadou_io_clicked)
        self.configSysContainer.add_child(self.btn_dadou_io)

        self.btn_xiaodou_io = MPushButton(
            text=tr("small_dou_io"),
            x=io_col_xs[1], y=io_btn_y, w=io_btn_w, h=io_btn_h
        )
        self.btn_xiaodou_io.clicked.connect(self.on_xiaodou_io_clicked)
        self.configSysContainer.add_child(self.btn_xiaodou_io)

        self._refresh_dou_io_buttons()

        self.tabWidget.addTab(self.configSysContainer, tr("system_params"))

    def _refresh_dou_io_buttons(self):
        """根据 GPIO 实际电平刷新大斗/小斗 IO 按钮配色（True=绿，False=红）。"""
        modules = Modules.instance()
        # 斗打开(True)对应低电平；读取不到（如仿真环境）按 False 处理
        dadou = getattr(modules, "outGPIODadou", None)
        xiaodou = getattr(modules, "outGPIOXiaodou", None)
        self._update_dou_io_button(self.btn_dadou_io, dadou.is_low() if dadou else False)
        self._update_dou_io_button(self.btn_xiaodou_io, xiaodou.is_low() if xiaodou else False)

    @staticmethod
    def _update_dou_io_button(btn, on):
        """IO 按钮配色：on=True 绿色，on=False 红色。"""
        if on:
            btn.bg_color = image.Color.from_rgb(76, 175, 80)
            btn.text_color = image.Color.from_rgb(255, 255, 255)
            btn.border_color = image.Color.from_rgb(56, 142, 60)
        else:
            btn.bg_color = image.Color.from_rgb(229, 57, 53)
            btn.text_color = image.Color.from_rgb(255, 255, 255)
            btn.border_color = image.Color.from_rgb(183, 28, 28)

    def on_dadou_io_clicked(self):
        """大斗 IO 手动翻转：True<->False，并同步按钮颜色。"""
        new_status = not Modules.instance().outGPIODadou.is_low()
        setDaDouStatus(new_status)
        self._update_dou_io_button(self.btn_dadou_io, new_status)

    def on_xiaodou_io_clicked(self):
        """小斗 IO 手动翻转：True<->False，并同步按钮颜色。"""
        new_status = not Modules.instance().outGPIOXiaodou.is_low()
        setXiaoDouStatus(new_status)
        self._update_dou_io_button(self.btn_xiaodou_io, new_status)

    def _update_ui_texts(self):
        """根据当前语言刷新所有已创建控件的文本。"""
        cfg = Modules.instance().config

        # 菜单页
        self.titleLabel.setText(tr("select_mode"))
        self.btn_debug.setText(tr("debug_mode"))
        self.btn_release.setText(tr("run_mode"))
        self.btn_config_prod.setText(tr("production_params"))
        self.btn_config_sys.setText(tr("system_params"))

        # Debug 页
        self.labelDisImgDebug.setText(tr("debug_image"))
        self.exit_debug_btn.setText(tr("exit"))

        # Release 页
        self.labelDisImgRel.setText(tr("running"))
        self.exit_release_btn.setText(tr("exit"))
        self.douStatus.setText(tr("status_stop"))
        self.actuatorStatus.setText(tr("actuator_stop"))
        self.btn_shutdown.setText(tr("shutdown"))
        # 语言切换后同步关机按钮字号上限：英文两行小字，其他语言原大小
        self.btn_shutdown.text_scale_max = 0.8 if current_language() == "en" else 1.0

        # 产量参数页
        self.title_config_prod.setText(tr("production_params"))
        self.exit_config_prod_btn.setText(tr("exit"))
        self.btn_language.setText(
            tr("language_btn_en") if cfg.language == "zh" else tr("language_btn_vi") if cfg.language == "en" else tr("language_btn_zh")
        )
        self.lb_dadouyici.setText(tr("big_dou"))
        self.btn_dadouyici.setText(str(cfg.dadouyici))
        self.lb_dadouyiciUnit.setText(tr("unit_pcs"))
        self.lb_xiaodouyici.setText(tr("small_dou"))
        self.btn_xiaodouyici.setText(str(cfg.xiaodouyici))
        self.lb_xiaodouyiciUnit.setText(tr("unit_pcs"))
        self.lb_zongshu.setText(tr("total"))
        self.btn_zongshu.setText(str(cfg.zongshu))
        self.lb_zongshuUnit.setText(tr("unit_pcs"))
        self.lb_wusuijian.setText(tr("disorder_percent"))
        self.btn_wusuijian.setText(str(cfg.wusuijian_fengexian))
        self.lb_wusuijianUnit.setText(tr("unit_percent"))

        # 系统参数页
        self.title_config_sys.setText(tr("system_params"))
        self.exit_config_sys_btn.setText(tr("exit"))
        self.lb_jiange.setText(tr("interval"))
        self.btn_jiange.setText(str(cfg.jiange))
        self.lb_jiangeUnit.setText(tr("unit_pcs"))
        self.lb_chufashijian.setText(tr("trigger_percent"))
        self.btn_chufashijian.setText(str(cfg.chufashijian))
        self.lb_chufashijianUnit.setText(tr("unit_percent"))
        self.lb_yanshichufashijian.setText(tr("delay_percent"))
        self.btn_yanshichufashijian.setText(str(cfg.yanshichufashijian))
        self.lb_yanshichufashijianUnit.setText(tr("unit_percent"))
        self.btn_dadou_io.setText(tr("big_dou_io"))
        self.btn_xiaodou_io.setText(tr("small_dou_io"))

    def on_language_clicked(self):
        """语言切换按钮槽函数。"""
        cfg = Modules.instance().config
        if cfg.language == "zh":
            cfg.language = "en"
        elif cfg.language == "en":
            cfg.language = "vi"
        else:
            cfg.language = "zh"
        set_language(cfg.language)
        self._update_ui_texts()
        cfg.save(path=Modules.instance().paths.config_path)

    def on_wusuijian_clicked(self):
        numberKeyBoard=NumberKeyBoard.create_centered(max_len=6)
        res=numberKeyBoard.exec()
        if res:
            value = numberKeyBoard.getValue()
            if value is None:
                return
            self.btn_wusuijian.setText(str(value))
            Modules.instance().config.wusuijian_fengexian = value
    # 槽函数定义
    def on_debug_clicked(self):
        print("Debug模式")
        self._last_menu_btn = self.btn_debug
        RunningInfo.instance().run_mode = RunMode.DEBUG
        self.tabWidget.setCurrentIndex(self.TAB_DEBUG)

    def on_release_clicked(self):
        print("Release模式")
        self._last_menu_btn = self.btn_release
        Modules.instance().actionQueue.clear()
        TaskGPIOManager.instance().startTaskManager()
        self.tabWidget.setCurrentIndex(self.TAB_RELEASE)
        RunningInfo.instance().run_mode = RunMode.RUN

    def on_config_prod_clicked(self):
        """产量参数页：无需密码，直接进入。"""
        print("产量参数")
        self._last_menu_btn = self.btn_config_prod
        self.tabWidget.setCurrentIndex(self.TAB_CONFIG_PROD)
        RunningInfo.instance().run_mode = RunMode.STOP

    def on_config_sys_clicked(self):
        """系统参数页：先验证密码，正确才进入；错误或取消留在菜单。"""
        print("系统参数")
        kb = NumberKeyBoard.create_centered(max_len=8, password=True)
        res = kb.exec()
        if not res:
            # 用户取消，留在菜单
            return
        if kb.getRawText() == self.SYSTEM_PARAMS_PASSWORD:
            self._last_menu_btn = self.btn_config_sys
            self.tabWidget.setCurrentIndex(self.TAB_CONFIG_SYS)
            RunningInfo.instance().run_mode = RunMode.STOP
            # 进入时按 GPIO 实际电平刷新 IO 按钮颜色（退出菜单时电平会被复位）
            self._refresh_dou_io_buttons()
        else:
            self._show_wrong_password_dialog()

    def _show_wrong_password_dialog(self):
        """密码错误提示弹窗，点确定后回到菜单。"""
        dialog = MDialog(120, 150, 400, 180)
        label = MLabel(text=tr("wrong_password"), x=dialog.x + 20, y=dialog.y + 40, w=dialog.w - 40, h=60, align="center")
        dialog.addWidget(label)
        ok_btn = MPushButton(text=tr("ok"), x=dialog.x + (dialog.w - 100) // 2, y=dialog.y + 110, w=100, h=50)
        ok_btn.clicked.connect(dialog.accept)
        dialog.addWidget(ok_btn)
        dialog.exec()

    def on_exit_to_menu(self):
        TaskGPIOManager.instance().stopTaskManager()
        TaskGPIOManager.instance().clearTask()
        # when exit debug or release mode, set dou to xiaodou open
        setXiaoDouStatus(True)
        setDaDouStatus(False)
        Modules.instance().config.save(path=Modules.instance().paths.config_path)

        RunningInfo.instance().run_mode = RunMode.STOP
        print("退出Debug")
        # 回到菜单：高亮最后进入过的界面按钮（绿色），其余恢复浅蓝灰
        self._highlight_menu_button(self._last_menu_btn)
        self.tabWidget.setCurrentIndex(self.TAB_MENU)

    def on_jiange_clicked(self):
        numberKeyBoard=NumberKeyBoard.create_centered(max_len=4)
        res=numberKeyBoard.exec()
        if res:
           value = numberKeyBoard.getValue()
           if value is None:
               return
           self.btn_jiange.setText(str(value))
           Modules.instance().config.jiange = value

    def on_yanshichufashijian_clicked(self):
        numberKeyBoard = NumberKeyBoard.create_centered(max_len=4)
        res = numberKeyBoard.exec()
        if res:
            value = numberKeyBoard.getValue()
            if value is None:
                return
            if value > 500:
                print("输入值大于500，已忽略。")
                return
            self.btn_yanshichufashijian.setText(str(value))
            Modules.instance().config.yanshichufashijian = value

    def on_chufashijian_clicked(self):
        numberKeyBoard=NumberKeyBoard.create_centered(max_len=4)
        res=numberKeyBoard.exec()
        if res:
           value = numberKeyBoard.getValue()
           if value is None:
               return
           self.btn_chufashijian.setText(str(value))
           Modules.instance().config.chufashijian = value

    def on_xiaodouyici_clicked(self):
        numberKeyBoard=NumberKeyBoard.create_centered(max_len=4)
        res=numberKeyBoard.exec()
        if res:
            value = numberKeyBoard.getValue()
            if value is None:
                return
            self.btn_xiaodouyici.setText(str(value))
            Modules.instance().config.xiaodouyici = value

    def on_dadouyici_clicked(self):
        numberKeyBoard=NumberKeyBoard.create_centered(max_len=4)
        res=numberKeyBoard.exec()
        if res:
           value = numberKeyBoard.getValue()
           if value is None:
               return
           self.btn_dadouyici.setText(str(value))
           Modules.instance().config.dadouyici = value

    def on_zongshu_clicked(self):
        numberKeyBoard=NumberKeyBoard.create_centered(max_len=4)
        res=numberKeyBoard.exec()
        if res:
           value = numberKeyBoard.getValue()
           if value is None:
               return
           self.btn_zongshu.setText(str(value))
           Modules.instance().config.zongshu = value
