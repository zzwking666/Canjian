from ImgProModule.Yolov11Coms import DetectImgProCom
from ImgProModule.Utility import ProcessResult,ProcessResultIndexMap,ClassIDWithName
from ImgProModule.ImgProComs.ImgPainterCom import ImgPainterCom,ConfigDrawRect
from maix import image
class ImgProContext:
    def __init__(self):
        self.processResult = ProcessResult()
        self.processResultIndexMap = ProcessResultIndexMap()
        self.classIDWithName=ClassIDWithName()

class ImgProCom:
    def count_left_of_split(self, img):
        try:
            from MaixCam.Modules import Modules
            cfg = Modules.instance().config
            split_percent = cfg.wusuijian_fengexian
            img_width = img.width() if hasattr(img, "width") else 640
            split_x = int((split_percent / 100.0) * img_width)
        except Exception:
            split_x = 320
        count = 0
        for obj in self.context.processResult:
            cx = obj["centralX"] if isinstance(obj, dict) else getattr(obj, "centralX", None)
            if cx is not None and cx > split_x:
                count += 1
        return count
    def __init__(self, DetectImgProCom: DetectImgProCom):
        self.detector = DetectImgProCom
        self.context = ImgProContext()
    
    def run(self, img):
        self.context.processResult = self.processImg(img)
        self.context.processResultIndexMap = self.getProcessResultIndexMap(self.context.processResult)
        return self.context
    
    def processImg(self, img):
     return self.detector.processImg(img)

    def getProcessResultIndexMap(self, results :ProcessResult):
        index_map = ProcessResultIndexMap()
        for idx, rect in enumerate(results):
            if rect.classid not in index_map:
                index_map[rect.classid] = []
            index_map[rect.classid].append(idx)
        return index_map
    
    def getMaskImg(self,img):
        processResult=self.context.processResult
        for obj in processResult:
            cfg=ConfigDrawRect()
            if obj.classid in self.context.classIDWithName:
                cfg.text=self.context.classIDWithName[obj.classid]
            else:
                cfg.text=str(obj.classid)
            ImgPainterCom.drawRectOnImg(img,obj,cfg)

        return img
    
    def getMaskImgWithountText(self, img):
        processResult = self.context.processResult
        # 获取分割线百分比和图像宽度
        try:
            from MaixCam.Modules import Modules
            cfg = Modules.instance().config
            split_percent = cfg.wusuijian_fengexian  # 0~100
            img_width = 640
            
        except Exception:
            split_percent = 50
            img_width = 640
        split_x = int((split_percent / 100.0) * img_width)

        # 绘制分割线（蓝色竖线）
        try:

                if 0 <= split_x < img.width():
                  split_x = int(split_x)
                  img_h = int(img.height())
                  
                  rectColor = image.Color.from_rgb(0, 0, 255)
                  img.draw_line(split_x, 0, split_x, img_h, color=rectColor, thickness=5)
                else:
                 print("split_x 越界:", split_x)

        except Exception as e:
           print("draw_line error:", e)

        for obj in processResult:
            cfg = ConfigDrawRect()
            cx = obj["centralX"] if isinstance(obj, dict) else getattr(obj, "centralX", None)

            
            if cx is not None and cx > split_x:
                cfg.rectColor = (0, 255, 0)  # 绿色
            else:
                
                cfg.rectColor = (255, 0, 0)  # 红色
            ImgPainterCom.drawRectOnImg(img, obj, cfg)

        return img
