from detect_utils import parking_line

from concurrent.futures import ThreadPoolExecutor
import datetime
import os
import PIL.Image
from PySide2 import QtCore
import weakref


ImageWidth = 3264
ImageHeight = 2448
ThumbWidth = 800
ThumbHeight = 600


class Camera:
    def __init__(self, camera_id):
        self.carports = []
        for port in parking_line[camera_id]:
            port = [(p[0]/ImageWidth*ThumbWidth, p[1]/ImageHeight*ThumbHeight) for p in port]
            self.carports.append(port)


class Image:
    def __init__(self, path):
        self._path = path
        filename = os.path.split(path)[1]
        hour, minute, second = filename[:8].split('_')
        t = datetime.datetime(2020, 1, 1, int(hour), int(minute), int(second)).timestamp()
        self.timestamp = int(t)
        self.thumbnail = None

    def load_thumbnail(self):
        img = PIL.Image.open(self._path)
        img.thumbnail([ThumbWidth, ThumbHeight])
        self.thumbnail = img

    def load_hd(self):
        return PIL.Image.open(self._path)


class ImageList(QtCore.QObject):
    _signal = QtCore.Signal(int)

    def __init__(self, path):
        super().__init__()
        self._path = path
        self._imgs = []
        for f in os.listdir(path):
            if not f.endswith('jpg'):
                continue
            img_path = os.path.join(path, f)
            if len(f) > 12:  # 图片自动改名
                new_path = os.path.join(path, f[11:19]+'.jpg')
                os.rename(img_path, new_path)
                img_path = new_path
            img = Image(img_path)
            self._imgs.append(img)
        self._pool = ThreadPoolExecutor(max_workers=4)
        self._observer = None

    @property
    def observer(self):
        return self._observer()

    @observer.setter
    def observer(self, observer):
        if self._observer:
            self._signal.disconnect(self._observer().img_update)
        if observer:
            self._signal.connect(observer.img_update)
        self._observer = weakref.ref(observer)

    def __del__(self):
        self._pool.shutdown(wait=False)

    def __len__(self):
        return len(self._imgs)

    def __getitem__(self, item):
        return self._imgs[item]

    def _async_load(self, idx, img):
        img.load_thumbnail()
        self._signal.emit(idx)

    def prefetch(self):
        for idx, img in enumerate(self._imgs):
            self._pool.submit(self._async_load, idx, img)


class Duration:
    def __init__(self, begin, end, rect):
        self.begin = begin
        self.end = end
        self.rect = rect


class Record:
    def __init__(self, port_idx, plate, begin, durations, end):
        self.port_idx = port_idx
        self.plate = plate
        self.begin = begin
        self.durations = [Duration(*d) for d in durations]
        self.end = end


class RecordList(QtCore.QObject):
    _signal = QtCore.Signal()

    def __init__(self):
        super().__init__()
        self._records = []
        self._observer = None

    @property
    def observer(self):
        return self._observer()

    @observer.setter
    def observer(self, observer):
        if self._observer:
            self._signal.disconnect(self._observer().record_update)
        if observer:
            self._signal.connect(observer.record_update)
        self._observer = weakref.ref(observer)

    @property
    def records(self):
        return list(self._records)

    def add_record(self, record):
        self._records.append(record)
        #todo: save
        self._signal.emit()

    def query_carports(self, timestamp):
        busy = set()
        for record in self._records:
            if record.begin <= timestamp < record.end:
                for idx in record.port_idx:
                    busy.add(idx)
        return busy
