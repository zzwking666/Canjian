from Mt.MApplication import MApplication
from Mt.MMainWindow import MMainWindow
from Mt.MPushButton import MPushButton
from Mt.MCheckBox import MCheckBox
from Mt.MLabel import MLabel
from Mt.MDialog import MDialog
from Mt.MTabWidget import MTabWidget
from Mt.GPIOBlink import GPIOBlink

from MaixCam.MainWindow import MaixCamMainWindow
from MaixCam.FrameCallBefor import FrameCallBefore
from MaixCam.RunningInfo import RunningInfo, RunMode, DouMode

from MaixCam.Modules import Modules
from maix import image
from MaixCam.TaskGPIOManager import TaskGPIOManager
from MaixCam.ResourceMonitor import ResourceMonitor
# ----------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------

def iniEnv():

    # 加载中文字体（越南语需确认设备上字体对 Â/Ă/Đ/Ê/Ô/Ơ/Ư 等字符的渲染效果，
    # 如发现声调符号缺失或字符重叠，可尝试换用 SourceHanSansSC-Regular.otf 或
    # 添加越南语专用字体文件）
    image.load_font("sourcehansans", "/maixapp/share/font/SourceHanSansCN-Regular.otf", size=32)
    image.set_default_font("sourcehansans")
    RunningInfo().instance().run_mode = RunMode.STOP
    Modules().instance()

def main():
    iniEnv()
    ResourceMonitor.instance().start()  # 每 200ms 打印一次 CPU/内存占用
    app = MApplication()
    win = MaixCamMainWindow(0, 0, app.img_width, app.img_height, margin=0)

    frameCallBefore = FrameCallBefore()

    app.setPreFrameCallback(frameCallBefore)

    app.setMainWindow(win)
    win.show()
    # interval_ms=10：主循环以约 100Hz 运行（触摸响应/GPIO 轮询足够），
    # 避免空转占满 CPU；算法处理在 FrameCallBefore 中已单独节流。
    app.exec(interval_ms=10)

def test():
    iniEnv()
    # Start the task manager and push one task (non-blocking)
    taskManager = TaskGPIOManager.instance()
    taskManager.startTaskManager()
    while True:
        import time
        Modules().instance().outGPIOXiaodou.setHight()
        time.sleep(1)
        Modules().instance().outGPIOXiaodou.setLow()
        time.sleep(1)


def test1():
    from maix import camera, display, image, nn, app

    detector = nn.YOLOv5(model="/root/models/yolov5s.mud", dual_buff=False)
    # detector = nn.YOLOv8(model="/root/models/yolov8n.mud", dual_buff=True)
    # detector = nn.YOLO11(model="/root/models/yolo11n.mud", dual_buff=True)

    cam = camera.Camera(detector.input_width(), detector.input_height(), detector.input_format())
    disp = display.Display()

    while not app.need_exit():
        img = cam.read()
        objs = detector.detect(img, conf_th=0.5, iou_th=0.45)
        for obj in objs:
            img.draw_rect(obj.x, obj.y, obj.w, obj.h, color=image.COLOR_RED)
            msg = f'{detector.labels[obj.class_id]}: {obj.score:.2f}'
            img.draw_string(obj.x, obj.y, msg, color=image.COLOR_RED)
        disp.show(img)

def test2():
    iniEnv()
    # Start the task manager and push one task (non-blocking)
    taskManager = TaskGPIOManager.instance()
    taskManager.startTaskManager()
    while True:
        Modules.instance().outGPIODadou.setHight()
        Modules.instance().outGPIOXiaodou.setHight()

def test_take_photo_by_trigger():
    """
    等待外部触发（GPIO 下降沿或按键）后拍摄一张照片。
    与 FrameCallBefore 的触发逻辑保持一致：
      - GPIO: 约定 1=低电平，0=高电平，下降沿 1->0 触发
      - 按键: KeyMonitor 的一次完整按下-释放触发
    此函数不依赖 Modules/AI 模型，直接初始化相机、GPIO 和按键监听。
    """
    from maix import time, gpio, display
    from CameraModule.CameraCom import CameraCom
    from MaixCam.Utilty import UtiltyPath
    from Mt.KeyMonitor import KeyMonitor, UserKey
    from Mt.GPIOBlink import GPIOBlink

    # 加载字体
    image.load_font("sourcehansans", "/maixapp/share/font/SourceHanSansCN-Regular.otf", size=32)
    image.set_default_font("sourcehansans")

    paths = UtiltyPath()
    camera = CameraCom(width=640, height=480, fmt=image.Format.FMT_RGB888, buff_num=1)
    inGPIO = GPIOBlink(pin_name=paths.pinIN_name, gpio_name=paths.gpioIN_name, initial=0, mode=gpio.Mode.IN)
    km = KeyMonitor.instance()
    disp = display.Display()

    gpio_prev_state = None
    print("等待外部触发...（GPIO 下降沿或按键）")

    while True:
        triggered = False

        # ---- GPIO 边沿检测，参考 FrameCallBefore.isTriggerByIO ----
        cur = None
        try:
            try:
                cur = inGPIO.value()
            except Exception:
                try:
                    cur = inGPIO.read()
                except Exception:
                    try:
                        cur = 1 if inGPIO.is_low() else 0
                    except Exception:
                        cur = None
        except Exception:
            cur = None

        if cur is not None:
            if gpio_prev_state is None:
                gpio_prev_state = cur
                print("GPIO initial state:", cur)
            else:
                # 状态变化时打印，便于观察外部 IO 信号
                if gpio_prev_state != cur:
                    print("GPIO changed:", gpio_prev_state, "->", cur)
                # 约定：下降沿 1 -> 0 触发
                if gpio_prev_state == 1 and cur == 0:
                    triggered = True
                gpio_prev_state = cur

        # ---- 按键触发，参考 FrameCallBefore.isTriggerByKey ----
        if not triggered and km.take_click(key_id=UserKey):
            triggered = True
            km.clear_clicks()

        # ---- 触发后读取一帧并显示，不保存图片 ----
        if triggered:
            camera.skip_frames(5)
            img = camera.read()
            disp.show(img)
            print("Triggered!")

        time.sleep_ms(10)

if __name__ == "__main__":
    #test_take_photo_by_trigger()
    #test()
    #test2()
    main()
