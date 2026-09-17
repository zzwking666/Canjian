import json
import os

class Config:
    def __init__(self):
        self.jiange = int(3)                 # 默认间隔：3
        self.yanshichufashijian = int(0)     # 默认延时触发时间：0
        self.chufashijian = int(90)          # 默认触发时间：90
        self.xiaodouyici = int(25)           # 默认小斗一次：25
        self.dadouyici = int(5)              # 默认大斗一次：5
        self.zongshu = int(35)               # 默认总数：35
        self.wusuijian_fengexian = int(25)   # 默认无绪茧分割线：25
        self.img_width = 640  # 默认图像宽度
        self.language = "zh"  # 默认语言：中文
        self._last_saved = {}  # path -> 上次成功写盘的内容（按路径跳过无变化写盘）

    def __str__(self):
        return (
            f"Config(jiange={self.jiange}, "
            f"yanshichufashijian={self.yanshichufashijian}, "
            f"chufashijian={self.chufashijian}, "
            f"xiaodouyici={self.xiaodouyici}, "
            f"dadouyici={self.dadouyici}, "
            f"zongshu={self.zongshu}, "
            f"wusuijian_fengexian={self.wusuijian_fengexian}, "
            f"language={self.language})"
        )

    def validate(self):
        """
        校验当前所有配置参数是否有效。
        返回 True 表示全部有效，False 表示存在 None 或类型错误。
        """
        try:
            return (
                self.jiange is not None and isinstance(self.jiange, int) and
                self.yanshichufashijian is not None and isinstance(self.yanshichufashijian, int) and
                self.chufashijian is not None and isinstance(self.chufashijian, int) and
                self.xiaodouyici is not None and isinstance(self.xiaodouyici, int) and
                self.dadouyici is not None and isinstance(self.dadouyici, int) and
                self.zongshu is not None and isinstance(self.zongshu, int) and
                self.wusuijian_fengexian is not None and isinstance(self.wusuijian_fengexian, int) and
                self.language is not None and self.language in ("zh", "en", "vi")
            )
        except Exception:
            return False

    def save(self, path):
        """
        将当前配置原子写入文件 path（JSON 格式）。
        若内容与上次一致则跳过写盘；否则先写临时文件并 fsync，
        再用 os.replace 原子替换，避免掉电损坏。
        返回 True 表示成功，失败返回 False。
        """
        try:
            d = {
                "jiange": self.jiange,
                "yanshichufashijian": self.yanshichufashijian,
                "chufashijian": self.chufashijian,
                "xiaodouyici": self.xiaodouyici,
                "dadouyici": self.dadouyici,
                "zongshu": self.zongshu,
                "wusuijian_fengexian": int(self.wusuijian_fengexian),
                "language": self.language,
            }
            # 内容未变化则跳过写盘，减少对存储介质的无谓写入
            new_data = json.dumps(d, ensure_ascii=False, indent=2)
            if self._last_saved.get(path) == new_data:
                return True
            # 确保目录存在
            dirn = os.path.dirname(path)
            if dirn and not os.path.exists(dirn):
                os.makedirs(dirn)
            tmp = path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(d, f, ensure_ascii=False, indent=2)
                f.flush()
                try:
                    os.fsync(f.fileno())
                except Exception:
                    pass
            if hasattr(os, "replace"):
                os.replace(tmp, path)
            else:
                os.rename(tmp, path)
            self._last_saved[path] = new_data
            return True
        except Exception:
            return False

    def load(self, path):
        """
        从文件 path 加载配置（JSON 格式）。
        返回 True 表示成功，失败返回 False（文件不存在、解析错误、
        或已知字段存在但为 None 视为参数丢失）。
        字段缺失时使用默认值；字段为 None 时触发备份回退。
        """
        try:
            if not os.path.exists(path):
                return False
            with open(path, "r", encoding="utf-8") as f:
                d = json.load(f)

            # 已知字段若存在但为 None，视为参数丢失，应由备份回退处理
            required_int_keys = [
                "jiange", "yanshichufashijian", "chufashijian",
                "xiaodouyici", "dadouyici", "zongshu", "wusuijian_fengexian"
            ]
            for key in required_int_keys:
                if key in d and d[key] is None:
                    return False
            if "language" in d and d["language"] is None:
                return False

            # 仅设置已知字段，避免注入未知属性；缺失时使用默认值
            self.jiange = int(d["jiange"]) if d.get("jiange") is not None else self.jiange
            self.yanshichufashijian = int(d["yanshichufashijian"]) if d.get("yanshichufashijian") is not None else self.yanshichufashijian
            self.chufashijian = int(d["chufashijian"]) if d.get("chufashijian") is not None else self.chufashijian
            self.xiaodouyici = int(d["xiaodouyici"]) if d.get("xiaodouyici") is not None else self.xiaodouyici
            self.dadouyici = int(d["dadouyici"]) if d.get("dadouyici") is not None else self.dadouyici
            self.zongshu = int(d["zongshu"]) if d.get("zongshu") is not None else self.zongshu
            self.wusuijian_fengexian = int(d["wusuijian_fengexian"]) if d.get("wusuijian_fengexian") is not None else self.wusuijian_fengexian
            lang = d.get("language")
            self.language = lang if lang in ("zh", "en", "vi") else "zh"
            return True
        except Exception:
            return False


def load_config_with_backup(config_path, backup_path):
    """
    加载配置，优先读取主配置文件；若主配置无效或缺失，则尝试备份配置。
    两者都失败时返回默认 Config 实例，并自动保存主配置和备份。
    返回加载或生成的 Config 对象。
    """
    def _load_from(path):
        if not os.path.exists(path):
            return None
        try:
            cfg = Config()
            if cfg.load(path) and cfg.validate():
                return cfg
        except Exception:
            pass
        return None

    def _save_cfg(cfg, path):
        try:
            cfg.save(path)
        except Exception:
            pass

    cfg_dir = os.path.dirname(config_path)
    if cfg_dir and not os.path.exists(cfg_dir):
        try:
            os.makedirs(cfg_dir)
        except Exception:
            pass

    # 1. 优先加载主配置
    cfg = _load_from(config_path)
    if cfg is not None:
        _save_cfg(cfg, backup_path)
        return cfg

    # 2. 主配置失败：尝试加载备份配置
    cfg = _load_from(backup_path)
    if cfg is not None:
        _save_cfg(cfg, config_path)
        return cfg

    # 3. 均失败：使用默认配置并保存两份
    cfg = Config()
    _save_cfg(cfg, config_path)
    _save_cfg(cfg, backup_path)
    return cfg

