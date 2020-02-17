from detect_utils import parking_line

from concurrent.futures import ThreadPoolExecutor
import datetime
import json
import os
import PIL.Image
from PySide2 import QtCore
import weakref


ImageWidth = 3264
ImageHeight = 2448


class Camera:
    def __init__(self, path):
        dst, camera_id = os.path.split(path)
        self.carports = []
        for port in parking_line[camera_id]:
            port = [(p[0]/ImageWidth, p[1]/ImageHeight) for p in port]
            self.carports.append(port)


class Image:
    def __init__(self, path, date):
        self._path = path
        year, month, day = date.split('_')
        filename = os.path.split(path)[1]
        hour, minute, second = filename[:8].split('_')
        t = datetime.datetime(int(year), int(month), int(day), int(hour), int(minute), int(second)).timestamp()
        self.timestamp = int(t)
        self.thumbnail = None

    def load_thumbnail(self, size):
        if not self.thumbnail:
            img = PIL.Image.open(self._path)
            img.thumbnail(size)
            self.thumbnail = img

    def load_hd(self):
        return PIL.Image.open(self._path)


class ImageList(QtCore.QObject):
    _signal = QtCore.Signal(int)

    def __init__(self, path):
        super().__init__()
        head, camera_id = os.path.split(path)
        _, date = os.path.split(head)
        self._camera_id = camera_id
        self._date = date
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
            img = Image(img_path, date)
            self._imgs.append(img)
        self._pool = ThreadPoolExecutor(max_workers=4)
        self._observer = None

    @property
    def observer(self):
        return self._observer

    @observer.setter
    def observer(self, observer):
        if self._observer:
            self._signal.disconnect(self._observer.img_update)
        if observer:
            self._signal.connect(observer.img_update)
            self._observer = weakref.proxy(observer)
        else:
            self._observer = None

    def __del__(self):
        self._pool.shutdown(wait=False)

    def __len__(self):
        return len(self._imgs)

    def __getitem__(self, item):
        return self._imgs[item]

    def _async_load(self, idx, size):
        self._imgs[idx].load_thumbnail(size)
        self._signal.emit(idx)

    def prefetch(self, size):
        for idx, img in enumerate(self._imgs):
            self._pool.submit(self._async_load, idx, size)


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
        self.durations = [Duration(**d) for d in durations]
        self.end = end

    def as_dict(self):
        return {
            'port_idx': self.port_idx,
            'plate': self.plate,
            'begin': self.begin,
            'durations': [d.__dict__ for d in self.durations],
            'end': self.end
        }


class RecordList(QtCore.QObject):
    _signal = QtCore.Signal()

    def __init__(self, path):
        super().__init__()
        dst, camera_id = os.path.split(path)
        self._label_path = os.path.join(dst, camera_id + '_label.json')
        self._record_path = os.path.join(dst, camera_id+'_record.json')
        if os.path.exists(self._record_path):
            with open(self._record_path, mode='r', encoding='utf-8') as file:
                records = json.load(file)
            self._records = [Record(**r) for r in records]
        else:
            self._records = []
        self._observer = None

    @property
    def observer(self):
        return self._observer

    @observer.setter
    def observer(self, observer):
        if self._observer:
            self._signal.disconnect(self._observer.record_update)
        if observer:
            self._signal.connect(observer.record_update)
            self._observer = weakref.proxy(observer)
        else:
            self._observer = None

    def __len__(self):
        return len(self._records)

    def __getitem__(self, item):
        return self._records[item]

    def add_record(self, record):
        self._records.append(record)
        self._signal.emit()

    def remove_record(self, record):
        self._records.remove(record)
        self._signal.emit()

    def query(self, timestamp):
        busy_carports = set()
        rects = []
        for record in self._records:
            if record.begin <= timestamp < record.end:
                for idx in record.port_idx:
                    busy_carports.add(idx)
                for d in record.durations:
                    if d.rect and d.begin <= timestamp <= d.end:
                        rects.append(d.rect)
        return busy_carports, rects

    def save(self):
        def strftime(timestamp):
            return datetime.datetime.fromtimestamp(timestamp).strftime('%H_%M_%S')

        # 直接保存records
        with open(self._record_path, mode='w', encoding='utf-8') as file:
            json.dump([r.as_dict() for r in self._records], file, ensure_ascii=False, indent=4)

        # 兼容旧label
        labels = []
        for r in self._records:
            time = []
            parking_pos = []

            # 入场直接2还是先1后2
            if r.begin != r.durations[0].begin:
                time.append(['1', strftime(r.begin)])
            time.append(['2', strftime(r.durations[0].begin)])

            for idx, d in enumerate(r.durations):
                if idx != 0:
                    # 除了第一段，每一段开头一定写
                    time.append(['2', strftime(d.begin)])
                if idx != len(r.durations)-1:
                    # 除了最后一段，都需要检查结尾
                    if d.end != r.durations[idx+1].begin:
                        time.append(['1', strftime(d.end)])
                if d.rect:
                    x, y, w, h = [int(p) for p in d.rect]
                    parking_pos.append([[x, y], [x+w, y+h]])

            # 离场直接0还是先1后0
            if r.end != r.durations[-1].end:
                time.append(['1', strftime(r.durations[-1].end)])
            time.append(['0', strftime(r.end)])

            d = {'plate': r.plate, 'parking_num': r.port_idx, 'time': time}
            if parking_pos:
                d['parking_pos'] = parking_pos
            labels.append(d)

        with open(self._label_path, mode='w', encoding='utf-8') as file:
            json.dump(labels, file, ensure_ascii=False, indent=4)
