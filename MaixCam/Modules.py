from CameraModule.CameraCom import CameraCom
from ImgProModule.Utility import AIVisionCreateConfig,ClassIDWithName
from ImgProModule.Yolov11Coms.DetectImgProCom import DetectImgProCom
from ImgProModule.ImgProComs.ImgProCom import ImgProCom
from maix import  display, image, app,gpio
from Mt.MApplication import MApplication
from Mt.KeyMonitor import KeyMonitor
from MaixCam.Config import Config, load_config_with_backup
from MaixCam.Utilty import UtiltyPath
from Mt.GPIOBlink import GPIOBlink
from MaixCam.Action import ActionQueue
from MaixCam.RunningInfo import RunningInfo, DouMode

class Modules:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(Modules, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, "_initialized") and self._initialized:
            return
        self.data = {}
        self._initialized = True
        self.ini()

    def defineVar(self):
        classIDWithName=ClassIDWithName()
        classIDWithName[0]=r"蚕茧"
        return classIDWithName
    
    def readConfig(self):
        self.paths = UtiltyPath()
        self.config = load_config_with_backup(
            self.paths.config_path, self.paths.config_backup_path
        )

    def ini(self):
        self.readConfig()

        engineConfig=AIVisionCreateConfig()
        engineConfig.model_path=Modules().paths.model_path
        engineConfig.dual_buff=False
        print("model_path:",engineConfig.model_path)
        
        self.engineCom=DetectImgProCom(engineConfig)
        self.imgProCom=ImgProCom(self.engineCom)
        #self.camera=CameraCom(width=self.engineCom.engine.input_width(),height=self.engineCom.engine.input_height(),fmt=self.engineCom.engine.input_format())
        self.camera=CameraCom(width=640,height=480,fmt=self.engineCom.engine.input_format(),buff_num=1)
        #self.camera.set_exposure(100)
        #self.camera.set_gain(0)

        self.imgProCom.context.classIDWithName=self.defineVar()
        self.disDebug=None
        self.disRelease=None
        self.countLabel=None
        self.countLabelRun=None
        self.douStatus=None
        self.actuatorStatus=None
        self.gpioStatus=None
        self.triggerCircleLabel_ms=None
        # 运行页资源监控角标（CPU/内存）
        self.sysInfoLabel=None

        self.outGPIODadou = GPIOBlink(pin_name=self.paths.pinOUT_nameDaDou, gpio_name=self.paths.gpioOUT_nameDaDou, initial=0)
        self.outGPIODadou.setHight()

        self.outGPIOXiaodou = GPIOBlink(pin_name=self.paths.pinOUT_nameXiaoDou, gpio_name=self.paths.gpioOUT_nameXiaoDou, initial=0)
        self.outGPIOXiaodou.setHight()

        self.inGPIO = GPIOBlink(pin_name=self.paths.pinIN_name, gpio_name=self.paths.gpioIN_name, initial=0,mode=gpio.Mode.IN)

        self.keyMonotor=KeyMonitor.instance()
        self.actionQueue=ActionQueue()

        # GPIO 测试定时器句柄（由 MApplication.instance().game_clock 驱动）
        # 周期性定时器（用于每个周期触发置高），以及一次性定时器（用于 high->low 延时）
        self._gpio_test_timer_periodic = None
        self._gpio_test_timer_off = None
        self._gpio_test_enabled = False

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = Modules()
        return cls._instance