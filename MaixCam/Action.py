def count_left_of_split(proResult, split_percent, img_width):
    """
    统计proResult中中心点在分割线左侧的目标数量。
    split_percent: 分割线位置百分比（0~1），如0.5表示一半
    img_width: 图像宽度
    """
    split_x = (split_percent / 100.0) * img_width
    count = 0

    for obj in proResult:
        cx = obj["centralX"] if isinstance(obj, dict) else getattr(obj, "centralX", None)
        if cx is not None and cx > split_x:

            count += 1
    return count
from ImgProModule.Utility import ProcessResultIndexMap,ProcessResult
from MaixCam.Config import Config

class Action:
    def __init__(self):
        self.isTrigger=bool(False)
        self.openXiaoDou=bool(False)
        self.openDaDou=bool(False)
        self.openShuangDou=bool(False)
        self.countSign=int(0)
        self.jiangeShu=int(0)

    def __str__(self):
        return (f"Action(isTrigger={self.isTrigger}, "
                f"openXiaoDou={self.openXiaoDou}, "
                f"openDaDou={self.openDaDou}, "
                f"countSign={self.countSign}, "
                f"jiangeShu={self.jiangeShu})")

def getAction(proResult:ProcessResult,cfg:Config,count:int)->Action:
    result = Action()

    # 假设 cfg.wusuijian_fengexian 为百分比（0~1），需要传入图像宽度
    # 你需要在调用getAction时传入img_width参数，或在cfg中加img_width
    # 这里假设有全局变量或cfg.img_width
    img_width = 640
    currentCount = count_left_of_split(proResult, cfg.wusuijian_fengexian, img_width)
    result.jiangeShu = cfg.jiange
    result.countSign = count
    
    if currentCount < cfg.zongshu:
        result.isTrigger = True
        if cfg.dadouyici == 0 and cfg.xiaodouyici == 0 and cfg.zongshu == 0:
            result.openXiaoDou = True
            
        elif cfg.xiaodouyici <= currentCount and currentCount < cfg.zongshu:
            result.openXiaoDou = True
            

        elif cfg.dadouyici <= currentCount and currentCount < cfg.xiaodouyici:
            result.openDaDou = True
            
        else:
            result.openShuangDou = True
            

    return result

def setDaDouStatus(status: bool) -> None:
    from MaixCam.Modules import Modules
    if status:
        Modules.instance().outGPIODadou.setLow()
    else:
        Modules.instance().outGPIODadou.setHight()

def setXiaoDouStatus(status: bool) -> None:
    from MaixCam.Modules import Modules
    if status:
        Modules.instance().outGPIOXiaodou.setLow()
    else:
        Modules.instance().outGPIOXiaodou.setHight()

from collections import deque
import threading
from typing import Optional, List, Iterator


class ActionQueue:
    """A simple thread-safe queue for Action objects with common utility methods.

    Methods:
    - enqueue(action): append an Action to the queue
    - dequeue(): remove and return the oldest Action, or None if empty
    - peek(): return the oldest Action without removing it, or None if empty
    - is_empty(): True when no items
    - size(): number of items
    - clear(): remove all items
    - to_list(): shallow copy of queued items as a list
    - extend(actions): enqueue multiple Action items
    - find(predicate): return first matching Action or None
    - __iter__/__len__/__repr__ implemented for convenience

    Thread-safety is provided by an internal Lock.
    """

    def __init__(self, maxlen: Optional[int] = 10):
        """
        :param maxlen: 队列最大长度，超过后自动丢弃最旧的动作。
                       默认 10，防止触发过快导致内存无限增长。
        """
        self._dq: deque = deque(maxlen=maxlen)
        self._lock = threading.Lock()

    def enqueue(self, action: Action) -> None:
        """Append an Action to the queue."""
        with self._lock:
            self._dq.append(action)

    def dequeue(self) -> Optional[Action]:
        """Remove and return the oldest Action. Return None if empty."""
        with self._lock:
            if not self._dq:
                return None
            return self._dq.popleft()

    def peek(self) -> Optional[Action]:
        """Return the oldest Action without removing it, or None if empty."""
        with self._lock:
            return self._dq[0] if self._dq else None

    def is_empty(self) -> bool:
        with self._lock:
            return len(self._dq) == 0

    def size(self) -> int:
        with self._lock:
            return len(self._dq)

    def clear(self) -> None:
        with self._lock:
            self._dq.clear()

    def to_list(self) -> List[Action]:
        """Return a shallow copy of the queue contents as a list."""
        with self._lock:
            return list(self._dq)

    def extend(self, actions: List[Action]) -> None:
        """Enqueue multiple Action items in order."""
        with self._lock:
            for a in actions:
                self._dq.append(a)

    def find(self, predicate) -> Optional[Action]:
        """Return first Action matching predicate(action) -> bool, or None."""
        with self._lock:
            for a in self._dq:
                try:
                    if predicate(a):
                        return a
                except Exception:
                    # don't let predicate exceptions break the scan
                    continue
            return None

    def __iter__(self) -> Iterator[Action]:
        # iterate over a snapshot to avoid holding lock during iteration
        with self._lock:
            snapshot = list(self._dq)
        return iter(snapshot)

    def __len__(self) -> int:
        return self.size()

    def __repr__(self) -> str:
        return f"ActionQueue(size={self.size()})"

