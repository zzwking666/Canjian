"""
简易国际化模块，支持中文/英文/越南语切换。
所有 UI 文本统一通过 tr(key) 获取，当前语言通过 set_language(lang) 设置。
"""

_TRANSLATIONS = {
    "zh": {
        "menu": "菜单",
        "select_mode": "请选择运行模式",
        "debug_mode": "调试模式",
        "run_mode": "运行模式",
        "config": "配置修改",
        "debug_image": "Debug模式下显示图像",
        "running": "Release模式下运行中...",
        "exit": "退出",
        "count_prefix": "当前识别数量:",
        "shutdown": "关机",
        "next_page": "下一页",
        "back": "返回",
        "more_config": "更多参数",
        "reserved_params": "预留参数页",
        "language_btn_zh": "中文",
        "language_btn_en": "English",
        "language_btn_vi": "Tiếng Việt",
        "interval": "间隔:",
        "unit_pcs": "个",
        "small_dou": "小斗一次:",
        "big_dou": "大斗一次:",
        "total": "总数:",
        "delay_percent": "延时触发时间:",
        "trigger_percent": "触发时间:",
        "disorder_percent": "无绪茧百分比:",
        "unit_percent": "%",
        "unit_ms": "ms",
        "status_big_dou": "大斗",
        "status_small_dou": "小斗",
        "status_both_dou": "双斗",
        "status_stop": "停止",
        "actuator_big_dou": "执行大斗",
        "actuator_small_dou": "执行小斗",
        "actuator_both_dou": "执行双斗",
        "actuator_stop": "执行停止",
        "gpio_signal": "有信号",
        "gpio_no_signal": "无信号",
        "shutdown_clicked": "关机按钮被点击！",
        "shutting_down": "正在关机",
        "ok": "确定",
        "cancel": "取消",
        "production_params": "产量参数",
        "system_params": "系统参数",
        "enter_password": "请输入密码",
        "wrong_password": "密码错误",
        "big_dou_io": "大斗IO控制",
        "small_dou_io": "小斗IO控制",
    },
    "en": {
        "menu": "Menu",
        "select_mode": "Select Mode",
        "debug_mode": "Debug Mode",
        "run_mode": "Run Mode",
        "config": "Settings",
        "debug_image": "Debug Image",
        "running": "Running...",
        "exit": "Exit",
        "count_prefix": "Count:",
        "shutdown": "Power\nOff",
        "next_page": "Next",
        "back": "Back",
        "more_config": "More Params",
        "reserved_params": "Reserved Params",
        "language_btn_zh": "中文",
        "language_btn_en": "English",
        "language_btn_vi": "Tiếng Việt",
        "interval": "Interval:",
        "unit_pcs": "pcs",
        "small_dou": "Small Dou:",
        "big_dou": "Big Dou:",
        "total": "Total:",
        "delay_percent": "Delay:",
        "trigger_percent": "Trigger:",
        "disorder_percent": "No-end Cocoon:",
        "unit_percent": "%",
        "unit_ms": "ms",
        "status_big_dou": "Big Dou",
        "status_small_dou": "Small Dou",
        "status_both_dou": "Both Dou",
        "status_stop": "Stop",
        "actuator_big_dou": "Act Big",
        "actuator_small_dou": "Act Small",
        "actuator_both_dou": "Act Both",
        "actuator_stop": "Act Stop",
        "gpio_signal": "Signal",
        "gpio_no_signal": "No Signal",
        "shutdown_clicked": "Shutdown button clicked!",
        "shutting_down": "Shutting down",
        "ok": "OK",
        "cancel": "Cancel",
        "production_params": "Production",
        "system_params": "System",
        "enter_password": "Enter Password",
        "wrong_password": "Wrong Password",
        "big_dou_io": "Big Dou IO",
        "small_dou_io": "Small Dou IO",
    },
    "vi": {
        "menu": "Trình đơn",
        "select_mode": "chọn chế độ",
        "debug_mode": "Chế độ gỡ lỗi",
        "run_mode": "chỉnh chế độ",
        "config": "sửa tham số",
        "debug_image": "Hiển thị hình ảnh ở chế độ gỡ lỗi",
        "running": "Đang chạy ở chế độ phát hành...",
        "exit": "thoát",
        "count_prefix": "Số lượng nhận dạng hiện tại:",
        "shutdown": "tắt máy",
        "next_page": "trang sau",
        "back": "Quay lại",
        "more_config": "Tham số khác",
        "reserved_params": "Trang tham số dự phòng",
        "language_btn_zh": "中文",
        "language_btn_en": "English",
        "language_btn_vi": "Tiếng Việt",
        "interval": "khoảng\ncách",
        "unit_pcs": "cái",
        "small_dou": "vợt nhỏ",
        "big_dou": "vợt to",
        "total": "Tổng số",
        "delay_percent": "TG kích\nhoạt trễ",
        "trigger_percent": "TG kích\nhoạt",
        "disorder_percent": "Kén không\nđầu mối",
        "unit_percent": "%",
        "unit_ms": "ms",
        "status_big_dou": "vợt to",
        "status_small_dou": "vợt nhỏ",
        "status_both_dou": "vợt 2",
        "status_stop": "Dừng",
        "actuator_big_dou": "chạy vợt to",
        "actuator_small_dou": "chạy vợt nhỏ",
        "actuator_both_dou": "chạy 2 vợt",
        "actuator_stop": "Thực hiện dừng",
        "gpio_signal": "có tín hiệu",
        "gpio_no_signal": "không tín hiệu",
        "shutdown_clicked": "Nút tắt máy đã được nhấn!",
        "shutting_down": "Đang tắt máy",
        "ok": "Đồng ý",
        "cancel": "Hủy",
        "production_params": "Sản xuất",
        "system_params": "Hệ thống",
        "enter_password": "Nhập mật khẩu",
        "wrong_password": "Sai mật khẩu",
        "big_dou_io": "IO vợt to",
        "small_dou_io": "IO vợt nhỏ",
    },
}

_language = "zh"


def set_language(lang):
    """设置当前语言，仅接受 'zh'、'en' 或 'vi'。"""
    global _language
    if lang in _TRANSLATIONS:
        _language = lang
    else:
        _language = "zh"


def current_language():
    """返回当前语言代码。"""
    return _language


def tr(key):
    """
    根据当前语言返回 key 对应的文本。
    若当前语言或 key 不存在，则依次回退到中文、最后返回 key 本身。
    """
    text = _TRANSLATIONS.get(_language, {}).get(key)
    if text is None:
        text = _TRANSLATIONS["zh"].get(key, key)
    return text
