import unittest

from MaixCam.Config import Config
from MaixCam.I18n import current_language, set_language, tr


class TestI18n(unittest.TestCase):
    def test_vietnamese_language_is_supported(self):
        set_language("vi")
        self.assertEqual(current_language(), "vi")
        self.assertEqual(tr("select_mode"), "chọn chế độ")
        self.assertEqual(tr("run_mode"), "chỉnh chế độ")
        self.assertEqual(tr("exit"), "thoát")
        self.assertEqual(tr("big_dou"), "vợt to")
        self.assertEqual(tr("small_dou"), "vợt nhỏ")
        self.assertEqual(tr("total"), "Tổng số")
        self.assertEqual(tr("trigger_percent"), "TG kích\nhoạt")
        self.assertEqual(tr("delay_percent"), "TG kích\nhoạt trễ")
        self.assertEqual(tr("disorder_percent"), "Kén không\nđầu mối")
        self.assertEqual(tr("next_page"), "trang sau")
        self.assertEqual(tr("shutdown"), "tắt máy")
        self.assertEqual(tr("actuator_both_dou"), "chạy 2 vợt")
        self.assertEqual(tr("actuator_small_dou"), "chạy vợt nhỏ")
        self.assertEqual(tr("actuator_big_dou"), "chạy vợt to")
        self.assertEqual(tr("config"), "sửa tham số")
        self.assertEqual(tr("unit_pcs"), "cái")
        self.assertEqual(tr("production_params"), "Sản xuất")
        self.assertEqual(tr("system_params"), "Hệ thống")
        self.assertEqual(tr("enter_password"), "Nhập mật khẩu")
        self.assertEqual(tr("wrong_password"), "Sai mật khẩu")

    def test_config_accepts_vietnamese_language(self):
        cfg = Config()
        cfg.language = "vi"
        self.assertEqual(cfg.language, "vi")


if __name__ == "__main__":
    unittest.main()
