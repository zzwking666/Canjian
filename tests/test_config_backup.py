"""
Config 备份回退加载测试。

验证主配置缺失、损坏或包含 null 字段时，能自动使用备份配置；
两者都失败时回退到默认值。
"""
import json
import os
import tempfile
import unittest

from MaixCam.Config import Config, load_config_with_backup


class TestConfigBackupFallback(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.tmpdir, "config.json")
        self.backup_path = os.path.join(self.tmpdir, "config_backup.json")

    def tearDown(self):
        for p in (self.config_path, self.backup_path):
            if os.path.exists(p):
                os.remove(p)
        os.rmdir(self.tmpdir)

    def _write(self, path, **overrides):
        """写入一个有效的配置文件，可覆盖部分字段。"""
        d = {
            "jiange": 3,
            "yanshichufashijian": 0,
            "chufashijian": 90,
            "xiaodouyici": 25,
            "dadouyici": 5,
            "zongshu": 35,
            "wusuijian_fengexian": 25,
            "language": "zh",
        }
        d.update(overrides)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, indent=2)

    def test_missing_main_uses_default_and_creates_both(self):
        """主配置和备份都不存在时使用默认值并保存两份。"""
        cfg = load_config_with_backup(self.config_path, self.backup_path)
        self.assertIsInstance(cfg, Config)
        self.assertEqual(cfg.chufashijian, 90)
        self.assertTrue(os.path.exists(self.config_path))
        self.assertTrue(os.path.exists(self.backup_path))

    def test_valid_main_creates_backup(self):
        """主配置有效时加载主配置并生成备份。"""
        self._write(self.config_path, chufashijian=120)
        cfg = load_config_with_backup(self.config_path, self.backup_path)
        self.assertEqual(cfg.chufashijian, 120)
        self.assertTrue(os.path.exists(self.backup_path))
        backup = Config()
        backup.load(self.backup_path)
        self.assertEqual(backup.chufashijian, 120)

    def test_corrupt_main_falls_back_to_backup(self):
        """主配置损坏时自动加载备份配置，并用备份覆盖主配置。"""
        self._write(self.backup_path, chufashijian=77)
        with open(self.config_path, "w", encoding="utf-8") as f:
            f.write("{not valid json")

        cfg = load_config_with_backup(self.config_path, self.backup_path)
        self.assertEqual(cfg.chufashijian, 77)

        # 主配置应被备份覆盖
        restored = Config()
        restored.load(self.config_path)
        self.assertEqual(restored.chufashijian, 77)

    def test_invalid_main_falls_back_to_backup(self):
        """主配置参数不合法时自动加载备份配置。"""
        self._write(self.backup_path, chufashijian=66)
        self._write(self.config_path, chufashijian="not-a-number")

        cfg = load_config_with_backup(self.config_path, self.backup_path)
        self.assertEqual(cfg.chufashijian, 66)

    def test_null_field_in_main_falls_back_to_backup(self):
        """主配置中存在 null 字段时视为参数丢失，加载备份配置。"""
        self._write(self.backup_path, xiaodouyici=3)
        self._write(self.config_path, xiaodouyici=None)

        cfg = load_config_with_backup(self.config_path, self.backup_path)
        self.assertEqual(cfg.xiaodouyici, 3)

        # 主配置应被备份覆盖
        restored = Config()
        restored.load(self.config_path)
        self.assertEqual(restored.xiaodouyici, 3)

    def test_both_corrupt_uses_default(self):
        """主配置和备份都损坏时使用默认值并保存两份。"""
        for p in (self.config_path, self.backup_path):
            with open(p, "w", encoding="utf-8") as f:
                f.write("broken")

        cfg = load_config_with_backup(self.config_path, self.backup_path)
        self.assertIsInstance(cfg, Config)
        self.assertEqual(cfg.chufashijian, 90)


if __name__ == "__main__":
    unittest.main()
