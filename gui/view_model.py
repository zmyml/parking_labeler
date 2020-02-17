from .model import ImageWidth, ImageHeight, Camera, ImageList, Record, RecordList
from .view import OpenDialog, ErrorDialog, MainWindow
import datetime
from functools import reduce
import PIL.ImageQt
from PySide2 import QtCore, QtGui, QtWidgets


ImageViewWidth = 800
ImageViewHeight = 600


def _strftime(timestamp):
    return datetime.datetime.fromtimestamp(timestamp).strftime('%H_%M_%S')


class ImageVM(QtCore.QObject):
    def __init__(self, path, img_widget, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.img_list = ImageList(path)
        self.img_list.observer = self
        self.img_list.prefetch([800, 600])
        self._img_widget = img_widget
        self._img_widget.scroll_bar.setRange(0, len(self.img_list) - 1)
        self._img_widget.scroll_bar.setValue(0)
        self._idx = 0
        self._zoom = False
        self._qimg = None

    def _update_img(self, x=None, y=None):
        time_str = _strftime(self.img_list[self.idx].timestamp)

        if self._zoom:
            img = self.img.load_hd()
            x = max(int(x / ImageViewWidth * ImageWidth), ImageViewWidth//2)
            x = min(x, ImageWidth - ImageViewWidth//2)
            y = max(int(y / ImageViewHeight * ImageHeight), ImageViewHeight//2)
            y = min(y, ImageHeight - ImageViewHeight//2)
            img = img.crop((x - ImageViewWidth//2, y - ImageViewHeight//2,
                            x + ImageViewWidth//2, y + ImageViewHeight//2))
        else:
            img = self.img.thumbnail

        if img:
            self._qimg = PIL.ImageQt.ImageQt(img)
            qpixmap = QtGui.QPixmap.fromImage(self._qimg)
        else:
            self._qimg = None
            qpixmap = None

        self._img_widget.time_label.setText(time_str)
        self._img_widget.img_label.setPixmap(qpixmap)
        self._img_widget.overlay_widget.setHidden(self._zoom)

    @property
    def img(self):
        return self.img_list[self.idx]

    @QtCore.Slot(int)
    def img_update(self, idx):
        if idx == self.idx:
            self.idx = idx

    @property
    def idx(self):
        return self._idx

    @idx.setter
    def idx(self, idx):
        self._idx = idx
        self._zoom = False
        self._update_img()

    def zoom(self, x, y):
        self._zoom = not self._zoom
        self._update_img(x, y)


class RecordVM(QtCore.QObject):
    def __init__(self, path, table_widget, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._table_widget = table_widget
        self._record_list = RecordList(path)
        self._record_list.observer = self
        self.record_update()
        self.parent()

    @property
    def idx(self):
        indexes = self._table_widget.selectedIndexes()
        if indexes:
            return indexes[0].row()
        else:
            return -1

    @idx.setter
    def idx(self, idx):
        self._table_widget.selectRow(idx)

    @QtCore.Slot()
    def record_update(self):
        self._record_list.save()

        self._table_widget.reset()
        self._table_widget.setRowCount(len(self._record_list))

        for idx in range(len(self._record_list)):
            record = self._record_list[idx]

            if len(record.port_idx) == 1:
                port_idx = str(record.port_idx[0])
            else:
                port_idx = reduce(lambda a, b: f'{a},{b}', record.port_idx)
            item0 = QtWidgets.QTableWidgetItem()
            item0.setText(port_idx)
            self._table_widget.setItem(idx, 0, item0)

            item1 = QtWidgets.QTableWidgetItem()
            item1.setText(record.plate)
            self._table_widget.setItem(idx, 1, item1)

            begin = _strftime(record.begin)
            item2 = QtWidgets.QTableWidgetItem()
            item2.setText(begin)
            self._table_widget.setItem(idx, 2, item2)

            durations = []
            for d in record.durations:
                s = f'[{_strftime(d.begin)}, {_strftime(d.end)})'
                if d.rect:
                    s += f'@{d.rect}'
                durations.append(s)
            durations = reduce(lambda a, b: f'{a}; {b}', durations)
            item3 = QtWidgets.QTableWidgetItem()
            item3.setText(durations)
            self._table_widget.setItem(idx, 3, item3)

            end = _strftime(record.end)
            item4 = QtWidgets.QTableWidgetItem()
            item4.setText(end)
            self._table_widget.setItem(idx, 4, item4)

        self._table_widget.update()

    def previous(self):
        if 0 <= self.idx - 1 < len(self._record_list):
            self.idx -= 1

    def next(self):
        if 0 <= self.idx + 1 < len(self._record_list):
            self.idx += 1

    def add(self, record):
        self._record_list.add_record(record)

    def remove(self):
        if 0 <= self.idx < len(self._record_list):
            record = self._record_list[self.idx]
            self._record_list.remove_record(record)
            return record
        return None

    def query(self, timestamp):
        return self._record_list.query(timestamp)


class EditVM:
    def __init__(self, edit_widget, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._edit_widget = edit_widget
        self._begin = None
        self._stable = None
        self._unstable = None
        self._rect = None
        self._durations = []
        self._end = None
        self._record = None

    def _update_durations(self):
        if not self._durations:
            self._edit_widget.duration_edit.setText('')
            return
        text = []
        for d in self._durations:
            stable_str = _strftime(d['begin']) if d['begin'] else ''
            unstable_str = _strftime(d['end']) if d['end'] else ''
            rect = str(d['rect']) if d['rect'] else ''
            s = f'{stable_str};{unstable_str};{rect}'
            text.append(s)
        text = reduce(lambda a, b: f'{a}\n{b}', text)
        self._edit_widget.duration_edit.setText(text)

    def _reset(self):
        self._begin = None
        self._stable = None
        self._unstable = None
        self._rect = None
        self._durations = []
        self._end = None
        self._record = None
        self._edit_widget.port_edit.setText('')
        self._edit_widget.plate_edit.setText('')
        self._edit_widget.begin_edit.setText('')
        self._edit_widget.stable_edit.setText('')
        self._edit_widget.unstable_edit.setText('')
        self._edit_widget.end_edit.setText('')
        self._edit_widget.rect_edit.setText('')
        self._edit_widget.duration_edit.setText('')
        self._edit_widget.mode_label.setText('添加记录')

    def begin(self, timestamp):
        self._begin = timestamp
        time = _strftime(timestamp)
        self._edit_widget.begin_edit.setText(time)

    def stable(self, timestamp):
        self._stable = timestamp
        time = _strftime(timestamp)
        self._edit_widget.stable_edit.setText(time)

    def unstable(self, timestamp):
        self._unstable = timestamp
        time = _strftime(timestamp)
        self._edit_widget.unstable_edit.setText(time)

    def end(self, timestamp):
        self._end = timestamp
        time = _strftime(timestamp)
        self._edit_widget.end_edit.setText(time)

    def rect(self, rect):
        if rect is None:
            self._rect = None
            self._edit_widget.rect_edit.setText('')
        else:
            self._rect = [int(rect[0]/ImageViewWidth*ImageWidth), int(rect[1]/ImageViewHeight*ImageHeight),
                          int(rect[2]/ImageViewWidth*ImageWidth), int(rect[3]/ImageViewHeight*ImageHeight)]
            self._edit_widget.rect_edit.setText(f'{self._rect}')

    def add_duration(self):
        d = {'begin': self._stable, 'end': self._unstable, 'rect': self._rect}
        self._stable = None
        self._unstable = None
        self._rect = None
        self._edit_widget.stable_edit.setText('')
        self._edit_widget.unstable_edit.setText('')
        self._edit_widget.rect_edit.setText('')
        self._durations.append(d)
        self._update_durations()

    def remove_duration(self):
        if self._durations:
            self._durations.pop(-1)
            self._update_durations()

    def confirm(self, first_t, last_t):
        port_idx = self._edit_widget.port_edit.text()
        port_idx = [int(s) for s in port_idx.split(',')]
        if not port_idx:
            raise ValueError('泊位号异常')

        plate = self._edit_widget.plate_edit.text()

        begin = self._begin
        if not begin:
            begin = first_t
        end = self._end
        if not end:
            end = last_t + 1

        d = {'begin': self._stable, 'end': self._unstable, 'rect': self._rect}
        self._durations.append(d)

        multi = len(port_idx) > 1
        if multi:
            if not self._durations:
                raise ValueError('跨车位必须标包围盒')
            for d in self._durations:
                if not d['rect']:
                    raise ValueError('跨车位必须标包围盒')

        durations = []
        for idx, d in enumerate(self._durations):
            d = dict(d)
            if d['begin'] is None:
                if idx == 0:
                    d['begin'] = begin
                else:
                    raise ValueError(f'第{idx}个停稳时段没有开始时间')
            if d['end'] is None:
                if idx == len(self._durations)-1:
                    d['end'] = end
                else:
                    next_d = self._durations[idx+1]
                    if next_d[0]:
                        d['end'] = next_d['begin']
                    else:
                        raise ValueError(f'第{idx+1}个停稳时段没有开始时间')
            durations.append(d)

        record = Record(port_idx, plate, begin, durations, end)
        self._reset()
        return record

    def cancel(self):
        record = self._record
        self._reset()
        return record

    def edit(self, record):
        self._record = record
        if len(record.port_idx) == 1:
            port_idx = str(record.port_idx[0])
        else:
            port_idx = reduce(lambda a, b: f'{a},{b}', record.port_idx)
        self._edit_widget.port_edit.setText(port_idx)
        self._edit_widget.plate_edit.setText(record.plate)
        self.begin(record.begin)
        d = record.durations.pop(-1)
        self.stable(d.begin)
        self.unstable(d.end)
        self.end(record.end)
        self.rect(d.rect)
        self._durations = [d.__dict__ for d in record.durations]
        self._update_durations()
        self._edit_widget.mode_label.setText('编辑记录')


class ViewModel(QtCore.QObject):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._camera = None
        self._img_vm = None
        self._record_vm = None
        self._edit_vm = None
        self.main_win = MainWindow(self)

    def _setup(self, path):
        self._camera = Camera(path)
        self._img_vm = ImageVM(path, self.main_win.image_widget)
        self._record_vm = RecordVM(path, self.main_win.table_widget)
        self._edit_vm = EditVM(self.main_win.edit_widget)
        self.main_win.image_widget.setHidden(False)
        self.main_win.table_widget.setHidden(False)
        self.main_win.edit_widget.setHidden(False)
        self._draw()

    def _draw(self):
        busy, rects = self._record_vm.query(self._img_vm.img.timestamp)
        polys = []
        for idx, port in enumerate(self._camera.carports):
            points = [[int(p[0]*ImageViewWidth), int(p[1]*ImageViewHeight)] for p in port]
            polys.append({'points': points, 'highlight': idx in busy})
        rects = [[int(rect[0] / ImageWidth * ImageViewWidth),
                  int(rect[1] / ImageHeight * ImageViewHeight),
                  int(rect[2] / ImageWidth * ImageViewWidth),
                  int(rect[3] / ImageHeight * ImageViewHeight)] for rect in rects]
        self.main_win.image_widget.overlay_widget.polys = polys
        self.main_win.image_widget.overlay_widget.rects = rects

    @QtCore.Slot()
    def open(self):
        dialog = OpenDialog()
        if dialog.exec_():
            path = dialog.selectedFiles()[0]
            self._setup(path)

    @QtCore.Slot()
    def edit_record(self):
        if self._record_vm:
            record = self._record_vm.remove()
            if record:
                self._edit_vm.edit(record)
                self._draw()

    @QtCore.Slot()
    def remove_record(self):
        if self._record_vm:
            self._record_vm.remove()
            self._draw()

    @QtCore.Slot(int)
    def idx_update(self, idx):
        if self._img_vm:
            self._img_vm.idx = idx
            self._draw()

    @QtCore.Slot(float, float)
    def zoom(self, x, y):
        if self._img_vm:
            self._img_vm.zoom(x, y)

    @QtCore.Slot()
    def up(self):
        if self._record_vm:
            self._record_vm.previous()

    @QtCore.Slot()
    def down(self):
        if self._record_vm:
            self._record_vm.next()

    @QtCore.Slot()
    def begin(self):
        if self._edit_vm:
            self._edit_vm.begin(self._img_vm.img.timestamp)

    @QtCore.Slot()
    def stable(self):
        if self._edit_vm:
            self._edit_vm.stable(self._img_vm.img.timestamp)

    @QtCore.Slot()
    def unstable(self):
        if self._edit_vm:
            self._edit_vm.unstable(self._img_vm.img.timestamp)

    @QtCore.Slot()
    def end(self):
        if self._edit_vm:
            self._edit_vm.end(self._img_vm.img.timestamp)

    @QtCore.Slot()
    def rect(self):
        if self._edit_vm:
            rect = self.main_win.image_widget.overlay_widget.rect
            self._edit_vm.rect(rect)

    @QtCore.Slot()
    def add_duration(self):
        if self._edit_vm:
            self._edit_vm.add_duration()

    @QtCore.Slot()
    def remove_duration(self):
        if self._edit_vm:
            self._edit_vm.remove_duration()

    @QtCore.Slot()
    def confirm(self):
        if self._edit_vm:
            try:
                record = self._edit_vm.confirm(self._img_vm.img_list[0].timestamp, self._img_vm.img_list[-1].timestamp)
            except ValueError as e:
                dialog = ErrorDialog(e.args[0])
                dialog.exec_()
            else:
                self._record_vm.add(record)
                self._draw()

    @QtCore.Slot()
    def cancel(self):
        if self._edit_vm:
            record = self._edit_vm.cancel()
            if record:
                self._record_vm.add(record)
                self._draw()
