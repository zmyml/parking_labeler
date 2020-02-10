from .model import ImageWidth, ImageHeight, ThumbWidth, ThumbHeight, Camera, ImageList, Record, RecordList
from .view import open_dialog, error_dialog, MainWindow

import datetime
from functools import reduce
import os
from PIL import ImageQt
from PySide2 import QtCore, QtGui, QtWidgets


def _create_camera(path):
    camera_id = os.path.split(path)[1]
    return Camera(camera_id)


def _strftime(timestamp):
    return datetime.datetime.fromtimestamp(timestamp).strftime('%H_%M_%S')


class ViewModel:
    def __init__(self):
        self._camera = None
        self._img_list = None
        self._record_list = None

        self._main_win = MainWindow(self)

        self._qimg = None
        self._idx = 0
        self._zoom = False

        self._begin = None
        self._stable = None
        self._unstable = None
        self._rect = None
        self._durations = []
        self._end = None

    def _set_img_list(self, img_list):
        img_list.observer = self
        img_list.prefetch()
        self._zoom = False
        self._img_list = img_list
        self._reset_edit()
        self._main_win.scroll_bar.setRange(0, len(img_list) - 1)
        self._main_win.scroll_bar.setValue(0)
        self._main_win.img_widget.setHidden(False)
        self._main_win.edit_widget.setHidden(False)
        self._main_win.table_widget.setHidden(False)
        self._main_win.table_widget.reset()

    @QtCore.Slot()
    def open(self):
        dialog = open_dialog()
        if dialog.exec_():
            path = dialog.selectedFiles()[0]
            self._camera = _create_camera(path)
            self._set_img_list(ImageList(path))
            self._record_list = RecordList()
            self._record_list.observer = self

    @property
    def img(self):
        return self._img_list[self._idx]

    def _update_img_widget(self, is_hd, x=None, y=None):
        busy = self._record_list.query_carports(self.img.timestamp)
        polys = []
        for idx, port in enumerate(self._camera.carports):
            polys.append({'points': port, 'highlight': idx in busy})
        self._main_win.overlay_widget.set_polys(polys)

        time = _strftime(self.img.timestamp)
        if is_hd:
            img = self.img.load_hd()
            x = max(int(x / ThumbWidth * ImageWidth), ThumbWidth//2)
            x = min(x, ImageWidth - ThumbWidth//2)
            y = max(int(y / ThumbHeight * ImageHeight), ThumbHeight//2)
            y = min(y, ImageHeight - ThumbHeight//2)
            pil_img = img.crop((x - ThumbWidth//2, y - ThumbHeight//2, x + ThumbWidth//2, y + ThumbHeight//2))
        else:
            pil_img = self.img.thumbnail

        if pil_img is None:
            self._qimg = None
            qpixmap = None
        else:
            self._qimg = ImageQt.ImageQt(pil_img)
            qpixmap = QtGui.QPixmap.fromImage(self._qimg)
        self._main_win.img_label.setPixmap(qpixmap)
        self._main_win.time_label.setText(time)
        self._main_win.overlay_widget.setHidden(is_hd)

    @QtCore.Slot()
    def img_update(self, idx):
        if idx == self._idx:
            self._update_img_widget(False)

    @QtCore.Slot()
    def idx_update(self, idx):
        self._idx = idx
        self._update_img_widget(False)

    @QtCore.Slot(float, float)
    def zoom(self, x, y):
        if self._zoom:
            self._update_img_widget(False)
        else:
            self._update_img_widget(True, x, y)
        self._zoom = not self._zoom

    @QtCore.Slot()
    def begin(self):
        self._begin = self.img.timestamp
        time = _strftime(self.img.timestamp)
        self._main_win.begin_edit.setText(time)

    @QtCore.Slot()
    def stable(self):
        self._stable = self.img.timestamp
        time = _strftime(self.img.timestamp)
        self._main_win.stable_edit.setText(time)

    @QtCore.Slot()
    def unstable(self):
        self._unstable = self.img.timestamp
        time = _strftime(self.img.timestamp)
        self._main_win.unstable_edit.setText(time)

    @QtCore.Slot()
    def rect(self):
        self._rect = self._main_win.rect
        if self._rect is None:
            return
        text = f'{self._rect[0]},{self._rect[1]},{self._rect[2]},{self._rect[3]}'
        self._main_win.rect_edit.setText(text)

    def _update_durations(self):
        if not self._durations:
            self._main_win.duration_edit.setText('')
        text = []
        for d in self._durations:
            stable, unstable, rect = d
            stable_str = _strftime(stable) if stable else ''
            unstable_str = _strftime(unstable) if unstable else ''
            rect = f'{rect[0]},{rect[1]},{rect[2]},{rect[3]}' if rect else ''
            s = f'{stable_str};{unstable_str};{rect}'
            text.append(s)
        text = reduce(lambda a, b: f'{a}\n{b}', text)
        self._main_win.duration_edit.setText(text)

    @QtCore.Slot()
    def add_duration(self):
        d = [self._stable, self._unstable, self._main_win.rect]
        self._durations.append(d)
        self._update_durations()

    @QtCore.Slot()
    def remove_duration(self):
        if self._durations:
            self._durations.pop(-1)
            self._update_durations()

    @QtCore.Slot()
    def end(self):
        self._end = self.img.timestamp
        time = _strftime(self.img.timestamp)
        self._main_win.end_edit.setText(time)

    def _reset_edit(self):
        self._begin = None
        self._stable = None
        self._unstable = None
        self._rect = None
        self._durations = []
        self._end = None
        self._main_win.port_edit.setText('')
        self._main_win.plate_edit.setText('')
        self._main_win.begin_edit.setText('')
        self._main_win.stable_edit.setText('')
        self._main_win.unstable_edit.setText('')
        self._main_win.rect_edit.setText('')
        self._main_win.duration_edit.setText('')
        self._main_win.end_edit.setText('')

    @QtCore.Slot()
    def ok(self):
        if self._img_list is None:
            return

        try:
            port_idx = self._main_win.port_edit.toPlainText()
            port_idx = [int(s) for s in port_idx.split(',')]
            if not port_idx:
                raise ValueError('泊位号异常')

            plate = self._main_win.plate_edit.toPlainText()

            begin = self._begin
            if not begin:
                begin = self._img_list[0].timestamp
            end = self._end
            if not end:
                end = self._img_list[-1].timestamp+1

            if self._stable or self._unstable or self._rect:
                d = [self._stable, self._unstable, self._rect]
                self._durations.append(d)
            else:
                d = [self._begin, self._end, None]
                self._durations.append(d)

            multi = len(port_idx) > 1
            if multi:
                if not self._durations:
                    raise ValueError('跨车位必须标包围盒')
                for d in self._durations:
                    if not d[2]:
                        raise ValueError('跨车位必须标包围盒')

            durations = []
            for idx in range(len(self._durations)):
                d = list(self._durations[idx])
                if d[0] is None:
                    if idx == 0:
                        d[0] = begin
                    else:
                        raise ValueError(f'第{idx}个停稳时段没有开始时间')
                if d[1] is None:
                    if idx == len(self._durations)-1:
                        d[1] = end
                    else:
                        next_d = self._durations[idx+1]
                        if next_d[0]:
                            d[1] = next_d[0]
                        else:
                            raise ValueError(f'第{idx+1}个停稳时段没有开始时间')
                durations.append(d)

            record = Record(port_idx, plate, begin, durations, end)
            self._record_list.add_record(record)
            self._reset_edit()
            self._update_img_widget(False)
        except ValueError as e:
            dialog = error_dialog(e.args[0])
            dialog.exec_()

    @QtCore.Slot()
    def cancel(self):
        self._reset_edit()

    @QtCore.Slot()
    def record_update(self):
        self._main_win.table_widget.reset()
        self._main_win.table_widget.setRowCount(len(self._record_list.records))
        for idx, record in enumerate(self._record_list.records):
            if len(record.port_idx) == 1:
                port_idx = str(record.port_idx[0])
            else:
                port_idx = reduce(lambda a, b: f'{a},{b}', record.port_idx)
            item0 = QtWidgets.QTableWidgetItem()
            item0.setText(port_idx)
            self._main_win.table_widget.setItem(idx, 0, item0)

            item1 = QtWidgets.QTableWidgetItem()
            item1.setText(record.plate)
            self._main_win.table_widget.setItem(idx, 1, item1)

            begin = _strftime(record.begin)
            item2 = QtWidgets.QTableWidgetItem()
            item2.setText(begin)
            self._main_win.table_widget.setItem(idx, 2, item2)

            durations = []
            for d in record.durations:
                s = f'[{_strftime(d.begin)}, {_strftime(d.end)})'
                if d.rect:
                    s += f'@{d.rect}'
                durations.append(s)
            durations = reduce(lambda a, b: f'{a}; {b}', durations)
            item3 = QtWidgets.QTableWidgetItem()
            item3.setText(durations)
            self._main_win.table_widget.setItem(idx, 3, item3)

            end = _strftime(record.end)
            item4 = QtWidgets.QTableWidgetItem()
            item4.setText(end)
            self._main_win.table_widget.setItem(idx, 4, item4)
        self._main_win.table_widget.update()

    def run(self):
        self._main_win.show()
