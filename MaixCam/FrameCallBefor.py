from ImgProModule.Utility import ProcessResultIndexMap
from MaixCam.RunningInfo import RunningInfo, RunMode,DouMode
from MaixCam.Modules import Modules
from MaixCam.Action import Action,getAction,ActionQueue,setDaDouStatus,setXiaoDouStatus
from Mt.MApplication import MApplication
from MaixCam.TaskGPIOManager import TaskGPIOManager
from Mt.KeyMonitor import UserKey
from Mt.MWidget import mark_dirty
from MaixCam.I18n import tr
from MaixCam.SysMonitor import SysMonitor
from maix import time, image
import gc

class FrameCallBefore:
    def __init__(self):
        app = MApplication.instance()
        # 只使用引擎时钟（必须保证 app.game_clock 已创建）
        self._game_clock = app.game_clock
        # 以引擎时钟初始化 last 时间，避免首次比较出错
        now = self._now_ms()
        self._last_debug_ms = now
        self._last_run_ms = now
        self.disp = app.disp

        # 节流间隔（毫秒），按需调整
        # 频率 f(Hz) = 1000 / interval_ms
        self.debug_interval_ms = 10   # debug 模式下算法处理频率 (20Hz)
        self.run_interval_ms = 10    # 运行模式下算法处理频率 (20Hz)

        # 报警定时器句柄（GameClock Timer 对象），用于在 N ms 后自动关闭报警
        # 支持多个 IO（0=大斗, 1=小斗）各自独立的定时器句柄
        # 这样两个 IO 可以同时触发且互不覆盖定时器
        self._alarm_timers = {0: None, 1: None}

        # 新增：连续空检测计数与阈值（连续多少帧/周期未检测到物体才触发报警）
        self._alarm_counter = 0
        self._alarm_threshold = 2  # 根据需要调整（例如 3 次连续未检测到才报警）

        # 新增：GPIO 输入状态机
        # 约定：gpio 返回 1 表示低电平，0 表示高电平
        self._gpio_prev_state = None      # 上一次读取的 GPIO 值
        self._io_rise_start_ms = None     # 低电平持续计时起点
        self._gpio_valid = False          # 当前是否处于有效触发状态（已持续 10ms 低电平）
        self._gpio_triggered = False      # 本次有效信号是否已经触发过一次

        # 新增：动作计数器
        self.countSign=int(0)
        # 新增：用于计算两次 trigger 之间的时间间隔（毫秒）
        self._last_trigger_time_ms = None
        self._last_trigger_interval_ms = None

        # 新增：用于处理长按逻辑的变量
        self._alarm_press_start_ms = None
        self._alarm_long_pressed_triggered = False

        # 新增：gc 按时间触发（每 5 秒一次），减少内存碎片
        self._last_gc_ms = now
        self.gc_interval_ms = 5000

        # 新增：GPIO 读取节流缓存（最小读取间隔 20ms），_update_gpio_state 与
        # update_gpio_status 共享同一次读取结果
        self.gpio_read_interval_ms = 20
        self._gpio_last_read_ms = None
        self._gpio_cached_value = None

        # 新增：GPIO 指示灯当前电平（避免每帧重复设置颜色）
        self._gpio_status_level = None

        # 资源监控（CPU/内存）节流采样：与心跳重绘同节奏（3s）刷新运行页角标
        self._last_sysinfo_ms = None
        self._sysinfo_interval_ms = 3000

    def __call__(self):
        self.run()

    def _now_ms(self):
        # 仅使用 engine clock 的 unscaled 时间（毫秒）
        try:
            return int(self._game_clock.unscaled_total_ms)
        except Exception:
            # 兜底为 time.ticks_ms，理论上不会走到这里
            try:
                return int(time.ticks_ms())
            except Exception:
                return int(time.time() * 1000)

    def _elapsed_ms(self, now, last):
        # 直接相减并保证非负（引擎时钟应单调递增）
        diff = int(now - last)
        if diff < 0:
            diff = -diff
        return diff

    def run(self):
        mode = RunningInfo.instance().run_mode
        self.handle_long_press()
        self._update_gpio_state()
        self.update_gpio_status()
        self._update_sysinfo()
        if mode == RunMode.DEBUG:
            self.run_debug()
        elif mode == RunMode.STOP:
            self.run_stop()
        elif mode == RunMode.RUN:
            self.run_run()

        # 周期性触发垃圾回收（按时间节流），减少内存碎片
        now = self._now_ms()
        if self._elapsed_ms(now, self._last_gc_ms) >= self.gc_interval_ms:
            self._last_gc_ms = now
            try:
                gc.collect()
            except Exception:
                pass

    def run_debug(self):
        now = self._now_ms()
        elapsed = self._elapsed_ms(now, self._last_debug_ms)
        # 只有超过间隔才执行昂贵处理
        if elapsed < self.debug_interval_ms:
            return
        self._last_debug_ms = now

        camera = Modules.instance().camera
        imgProCom = Modules.instance().imgProCom

        # 读取并处理 —— 这是昂贵操作，已被节流

        camera.skip_frames(2)
        img = camera.read()
        imgProCom.run(img)

        processResult = imgProCom.context.processResultIndexMap

        maskImg = imgProCom.getMaskImgWithountText(img)

        mods = Modules.instance()
        if getattr(mods, "disDebug", None):
            mods.disDebug.setImage(maskImg)
            mods.countLabel.setText(str(len(imgProCom.context.processResult)))

    def run_stop(self):
        # 停止模式下可做低频维护任务，或直接 return
        return

    def _update_sysinfo(self):
        """节流 3s 采样整机/本进程 CPU 与内存，并刷新运行页监控角标。

        与心跳重绘同节奏：本函数在主循环帧前回调中执行，setText 标脏后
        当帧即随重绘上屏，无需额外的强制刷新。
        """
        now = self._now_ms()
        if self._last_sysinfo_ms is not None and \
                self._elapsed_ms(now, self._last_sysinfo_ms) < self._sysinfo_interval_ms:
            return
        self._last_sysinfo_ms = now
        try:
            mon = SysMonitor.instance()
            mon.sample()
            label = getattr(Modules.instance(), "sysInfoLabel", None)
            if label is not None:
                label.setText(mon.format())
        except Exception:
            # 监控失败不影响主流程
            pass
    
    def _set_actuator_status(self, key: str):
        """更新左上角执行机构状态按钮文本（安全回退）。"""
        actuator = getattr(Modules.instance(), "actuatorStatus", None)
        if actuator is not None:
            actuator.setText(tr(key))

    def ioDaDou_trigger(self,delayTime:int,actionTime:int):
        TaskGPIOManager.instance().pushTask(actionTime, 0,mode=DouMode.DaDouOnly,delay_ms=delayTime)
        self._set_actuator_status("actuator_big_dou")

    def ioXiaoDou_trigger(self,delayTime:int,actionTime:int):
        TaskGPIOManager.instance().pushTask(actionTime, 0,mode=DouMode.XiaoDouOnly,delay_ms=delayTime)
        self._set_actuator_status("actuator_small_dou")

    def ioShuangDou_trigger(self,delayTime:int,actionTime:int):
        TaskGPIOManager.instance().pushTask(actionTime, 0,mode=DouMode.BothDaDouXiaoDou,delay_ms=delayTime)
        self._set_actuator_status("actuator_both_dou")

    def ioStop_trigger(self,delayTime:int,actionTime:int):
        TaskGPIOManager.instance().pushTask(actionTime, 0,mode=DouMode.Stop,delay_ms=delayTime)
        self._set_actuator_status("actuator_stop")

    def _update_dou_status_by_action(self, action):
        """根据识别结果对应的 action 更新运行界面大小斗状态。"""
        dou_status = getattr(Modules.instance(), "douStatus", None)
        if dou_status is None:
            return
        if action.openDaDou:
            dou_status.setText(tr("status_big_dou"))
        elif action.openXiaoDou:
            dou_status.setText(tr("status_small_dou"))
        elif action.openShuangDou:
            dou_status.setText(tr("status_both_dou"))
        else:
            dou_status.setText(tr("status_stop"))

    def get_last_trigger_interval_ms(self):
        """返回上一次触发与本次触发之间的时间间隔（毫秒），如果尚无两次触发则返回 None。"""
        return self._last_trigger_interval_ms

    def trigger_actionDou(self):
        currentSign= self.countSign
        queue=Modules.instance().actionQueue
        if(queue.size()>0):
            action=queue.peek()
            if(action.countSign+action.jiangeShu<=currentSign):
                triggerIntervalMs = RunningInfo.instance().trigger_interval_ms
                cfg=Modules.instance().config
                # 这里的延时动作修改为0了，该参数现在用于延时触发拍照
                delayMs=0
                actionMs=triggerIntervalMs * cfg.chufashijian / 100
                if(action.isTrigger):
                    if(action.openDaDou):
                        self.ioDaDou_trigger(delayMs, actionMs)
                    elif(action.openXiaoDou):
                        self.ioXiaoDou_trigger(delayMs, actionMs)
                    elif(action.openShuangDou):
                        self.ioShuangDou_trigger(delayMs, actionMs)
                    action = queue.dequeue()
                else:
                    self.ioStop_trigger(delayMs, actionMs)
                    action = queue.dequeue()
            
            # 清理过期动作
            tempAction=queue.peek()
            while(queue.size()>0 and tempAction.countSign+tempAction.jiangeShu<=currentSign):
                tempAction = queue.dequeue()

    def caculate_trigger_interval_ms(self,now:int):
            try:
                if self._last_trigger_time_ms is not None:
                    interval = self._elapsed_ms(now, self._last_trigger_time_ms)
                    self._last_trigger_interval_ms = interval
                    try:
                        RunningInfo.instance().data['last_trigger_interval_ms'] = interval
                        RunningInfo.instance().trigger_interval_ms = interval
                    except Exception:
                        pass
                    try:
                        Modules.instance().triggerCircleLabel_ms.setText(f"{interval} ms")
                        pass
                    except Exception:
                        pass
                else:
                    # 首次触发
                    try:
                        #print(f"First trigger at {now} ms")
                        pass
                    except Exception:
                        pass
                # 更新最近一次触发时间
                self._last_trigger_time_ms = now
            except Exception:
                # 在任何异常情况下不要阻塞主流程
                pass

    def run_run(self):
        now = self._now_ms()
        elapsed = self._elapsed_ms(now, self._last_run_ms)
        # 只有超过间隔才执行昂贵处理
        if elapsed < self.run_interval_ms:
            return
        self._last_run_ms = now

        camera = Modules.instance().camera
        imgProCom = Modules.instance().imgProCom
        isTrigger=self.isTrigger()

        if isTrigger:
            # 计算 trigger 间隔
            self.caculate_trigger_interval_ms(now)
            camera.skip_frames(2)

            img = camera.read()
            imgProCom.run(img)
            processResult= imgProCom.context.processResult
            config=Modules.instance().config
           
            action = getAction(proResult=processResult, cfg=config,count=self.countSign)
            self.countSign+=1
            Modules.instance().actionQueue.enqueue(action)
            # 根据当前识别到的蚕茧数量更新大小斗显示
            self._update_dou_status_by_action(action)
            self.trigger_actionDou()

            maskImg = imgProCom.getMaskImgWithountText(img)
            mods = Modules.instance()
            if getattr(mods, "disRelease", None):
                mods.disRelease.setImage(maskImg)
                # 统计分割线左侧目标数量
                if hasattr(imgProCom, "count_left_of_split"):
                    left_count = imgProCom.count_left_of_split(img)
                else:
                    # 兼容旧版本
                    left_count = len(imgProCom.context.processResult)
                mods.countLabelRun.setText(str(left_count))

    def _read_gpio_value(self):
        """读取 GPIO 输入当前值（约定：1=低电平，0=高电平），读取失败返回 None。

        带 20ms 节流缓存：距上次真实读取不足 gpio_read_interval_ms 时直接返回
        缓存值。消抖逻辑基于时间戳而非采样次数，20ms 采样不影响 10ms 消抖判定，
        只会把触发响应延迟最多拉大 ~20ms。
        """
        now = self._now_ms()
        if self._gpio_last_read_ms is not None and \
                self._elapsed_ms(now, self._gpio_last_read_ms) < self.gpio_read_interval_ms:
            return self._gpio_cached_value

        gpioIn = Modules.instance().inGPIO
        try:
            try:
                value = gpioIn.value()
            except Exception:
                try:
                    value = gpioIn.read()
                except Exception:
                    try:
                        value = 1 if gpioIn.is_low() else 0
                    except Exception:
                        value = None
        except Exception:
            value = None

        self._gpio_last_read_ms = now
        self._gpio_cached_value = value
        return value

    def _update_gpio_state(self):
        """
        统一更新 GPIO 输入状态机（含 10ms 消抖）。
        结果保存在 self._gpio_valid 中：高电平持续 >=10ms 为 True，否则 False。
        """
        cur = self._read_gpio_value()

        if cur is None:
            # 无法读取时重置状态，避免误触发
            self._gpio_prev_state = None
            self._io_rise_start_ms = None
            self._gpio_valid = False
            return

        prev = self._gpio_prev_state
        if prev is None:
            # 首次读取仅记录，不触发
            self._gpio_prev_state = cur
            self._io_rise_start_ms = None
            self._gpio_valid = False
            return

        # 触发持续时间硬编码为 10 毫秒
        duration_ms = 10

        # 上升沿：1 -> 0（低电平变高电平），开始计时
        if prev == 1 and cur == 0:
            self._io_rise_start_ms = self._now_ms()

        if self._io_rise_start_ms is not None:
            if cur == 0:
                # 信号保持高电平，检查持续时间
                elapsed = self._elapsed_ms(self._now_ms(), self._io_rise_start_ms)
                if elapsed >= duration_ms:
                    self._gpio_valid = True
            else:
                # 信号提前变低，取消计时
                self._io_rise_start_ms = None
                self._gpio_valid = False

        self._gpio_prev_state = cur

    def update_gpio_status(self):
        """更新 Release 界面左下角的 GPIO 输入状态指示灯颜色，实时反映当前电平。"""
        gpio_status_btn = getattr(Modules.instance(), "gpioStatus", None)
        if gpio_status_btn is None:
            return
        cur = self._read_gpio_value()
        if cur is None or cur == self._gpio_status_level:
            return
        self._gpio_status_level = cur
        if cur == 1:
            # 低电平 -> 有信号 -> 绿色
            gpio_status_btn.bg_color = image.Color.from_rgb(80, 180, 80)
        else:
            # 高电平 -> 无信号 -> 红色
            gpio_status_btn.bg_color = image.Color.from_rgb(220, 80, 80)
        mark_dirty()

    def isTriggerByIO(self):
        """
        基于统一的 GPIO 状态机判断是否需要触发识别。
        当高电平持续 >=10ms 后首次调用返回 True，信号恢复低电平后重置。
        返回: bool
        """
        if self._gpio_valid and not self._gpio_triggered:
            self._gpio_triggered = True
            return True
        if not self._gpio_valid:
            self._gpio_triggered = False
        return False

    def isTriggerByKey(self):
        # 按下按键保存图片
        km = Modules.instance().keyMonotor
        if  km.take_click(key_id=UserKey):
            km.clear_clicks()
            return True
        return False

    def isTrigger(self):
        delayMs = Modules.instance().config.yanshichufashijian
        triggered = self.isTriggerByIO() or self.isTriggerByKey()
        if triggered:
            time.sleep_ms(delayMs)  # 延迟指定的毫秒数
        return bool(triggered)

    def handle_long_press(self):
        # 长按2秒切换 enable_alarm 的逻辑   
        now = self._now_ms()
        km = Modules.instance().keyMonotor
        try:    
            key_down = km.is_down(key_id=UserKey)
        except Exception:
            key_down = False

        if key_down:
            if self._alarm_press_start_ms is None:
                # 按下开始计时
                self._alarm_press_start_ms = now
                self._alarm_long_pressed_triggered = False
            else:
                # 已按下，检查是否达到2秒且未触发过
                if (not self._alarm_long_pressed_triggered) and (now - self._alarm_press_start_ms >= 2400):
                    self._alarm_long_pressed_triggered = True
                    self.exit_program()
                    try:
                        km.clear_clicks()
                    except Exception:
                        pass
        else:
            # 按键释放，重置长按检测状态
            self._alarm_press_start_ms = None
            self._alarm_long_pressed_triggered = False

    def exit_program(self):
        TaskGPIOManager.instance().stopTaskManager()
        TaskGPIOManager.instance().clearTask()
        MApplication.instance().exit()