from PySide2 import QtCore, QtGui, QtWidgets


def open_dialog():
    dialog = QtWidgets.QFileDialog()
    dialog.setFileMode(QtWidgets.QFileDialog.FileMode.Directory)
    dialog.setOption(QtWidgets.QFileDialog.Option.ShowDirsOnly)
    return dialog


def error_dialog(msg):
    dialog = QtWidgets.QDialog()
    label = QtWidgets.QLabel()
    label.setText(msg)
    button = QtWidgets.QPushButton()
    button.setText('确定')
    button.clicked.connect(dialog.accept)
    layout = QtWidgets.QVBoxLayout()
    layout.addWidget(label)
    layout.addWidget(button)
    dialog.setLayout(layout)
    return dialog


class OverlayWidget(QtWidgets.QWidget):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self._polys = []
        self._rect = None

    def set_polys(self, polys):
        self._polys = polys
        self.update()

    def set_rect(self, rect):
        self._rect = rect
        self.update()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing, True)
        for poly in self._polys:
            points = [QtCore.QPoint(*p) for p in poly['points']]
            points.append(points[0])
            pen = QtGui.QPen()
            if poly['highlight']:
                pen.setColor(QtCore.Qt.red)
            else:
                pen.setColor(QtCore.Qt.green)
            painter.setPen(pen)
            painter.drawPolyline(points)
        if self._rect:
            pen = QtGui.QPen()
            pen.setColor(QtCore.Qt.yellow)
            painter.setPen(pen)
            painter.drawRect(*self._rect)


class MainWindow(QtWidgets.QMainWindow):
    _zoom_signal = QtCore.Signal(float, float)

    def __init__(self, vm):
        super().__init__(None)
        self.setWindowTitle('停车记录标注')
        self.setFixedSize(1200, 800)

        self.img_widget = QtWidgets.QWidget(self)
        self.img_widget.setGeometry(0, 25, 800, 620)
        self.img_widget.setHidden(True)

        self.img_label = QtWidgets.QLabel(self.img_widget)
        self.img_label.setGeometry(0, 0, 800, 600)

        self.overlay_widget = OverlayWidget(self.img_widget)
        self.overlay_widget.setGeometry(0, 0, 800, 600)

        self.time_label = QtWidgets.QLabel(self.img_widget)
        self.time_label.setStyleSheet('color:black;font-size:40px;background-color:white;')
        self.time_label.setGeometry(10, 10, 160, 40)

        self.touch_widget = QtWidgets.QWidget(self.img_widget)
        self.touch_widget.setGeometry(0, 0, 800, 600)
        self.touch_widget.installEventFilter(self)

        self.scroll_bar = QtWidgets.QScrollBar(self.img_widget)
        self.scroll_bar.setOrientation(QtCore.Qt.Orientation.Horizontal)
        self.scroll_bar.setSingleStep(1)
        self.scroll_bar.valueChanged.connect(vm.idx_update)
        self.scroll_bar.setGeometry(0, 600, 800, 20)

        self.table_widget = QtWidgets.QTableWidget(self)
        self.table_widget.setColumnCount(5)
        self.table_widget.setColumnWidth(0, 80)
        self.table_widget.setColumnWidth(1, 100)
        self.table_widget.setColumnWidth(2, 100)
        self.table_widget.setColumnWidth(3, 400)
        self.table_widget.setColumnWidth(4, 100)
        self.table_widget.setHorizontalHeaderLabels(['泊位', '车牌', '入场时间', '停稳时段', '离场时间'])
        self.table_widget.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.table_widget.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.table_widget.setGeometry(0, 645, 800, 155)
        self.table_widget.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.table_widget.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.table_widget.verticalHeader().setHidden(True)
        self.table_widget.setHidden(True)

        self.edit_widget = QtWidgets.QWidget(self)
        self.edit_widget.setGeometry(800, 25, 400, 775)
        self.edit_widget.setHidden(True)

        port_label = QtWidgets.QLabel()
        port_label.setText('泊位')
        self.port_edit = QtWidgets.QTextEdit()
        self.port_edit.setPlaceholderText('跨车位用逗号分隔')
        self.port_edit.setMaximumHeight(25)
        self.port_edit.setFocus()

        plate_label = QtWidgets.QLabel()
        plate_label.setText('车牌')
        self.plate_edit = QtWidgets.QTextEdit()
        self.plate_edit.setPlaceholderText('双击图片可放大')
        self.plate_edit.setMaximumHeight(25)

        begin_label = QtWidgets.QLabel()
        begin_label.setText('入场时间')
        self.begin_edit = QtWidgets.QTextEdit()
        self.begin_edit.setPlaceholderText('按F1使用当前时间, 留空默认为第一张')
        self.begin_edit.setMaximumHeight(25)
        self.begin_edit.setEnabled(False)

        stable_label = QtWidgets.QLabel()
        stable_label.setText('停稳时间')
        self.stable_edit = QtWidgets.QTextEdit()
        self.stable_edit.setPlaceholderText('F2，留空默认为入场时间')
        self.stable_edit.setMaximumHeight(25)
        self.stable_edit.setEnabled(False)

        unstable_label = QtWidgets.QLabel()
        unstable_label.setText('移动时间')
        self.unstable_edit = QtWidgets.QTextEdit()
        self.unstable_edit.setPlaceholderText('F3，留空默认为离场/下个停稳时间')
        self.unstable_edit.setMaximumHeight(25)
        self.unstable_edit.setEnabled(False)

        rect_label = QtWidgets.QLabel()
        rect_label.setText('车辆位置')
        self.rect_edit = QtWidgets.QTextEdit()
        self.rect_edit.setPlaceholderText('按F5使用当前矩形，未跨车位不需要')
        self.rect_edit.setMaximumHeight(25)
        self.rect_edit.setEnabled(False)

        duration_label = QtWidgets.QLabel()
        duration_label.setText('已有停稳时段')
        self.duration_edit = QtWidgets.QTextEdit()
        self.duration_edit.setPlaceholderText('只有一个停稳时段或最后一个停稳时段不需要添加，设置好直接确定')
        self.duration_edit.setMaximumHeight(75)
        self.duration_edit.setEnabled(False)

        add_button = QtWidgets.QPushButton()
        add_button.setText('添加停稳时段 (F6)')
        add_button.clicked.connect(vm.add_duration)
        remove_button = QtWidgets.QPushButton()
        remove_button.setText('删除停稳时段 (F7)')
        remove_button.clicked.connect(vm.remove_duration)

        end_label = QtWidgets.QLabel()
        end_label.setText('离场时间')
        self.end_edit = QtWidgets.QTextEdit()
        self.end_edit.setPlaceholderText('F4，留空默认为未出场')
        self.end_edit.setMaximumHeight(25)
        self.end_edit.setEnabled(False)

        ok_btn = QtWidgets.QPushButton()
        ok_btn.setText('确定')
        ok_btn.clicked.connect(vm.ok)
        cancel_btn = QtWidgets.QPushButton()
        cancel_btn.setText('取消')
        cancel_btn.clicked.connect(vm.cancel)

        layout = QtWidgets.QGridLayout()
        layout.addWidget(port_label, 0, 0)
        layout.addWidget(self.port_edit, 0, 1)
        layout.addWidget(plate_label, 1, 0)
        layout.addWidget(self.plate_edit, 1, 1)
        layout.addWidget(begin_label, 2, 0)
        layout.addWidget(self.begin_edit, 2, 1)
        layout.addWidget(stable_label, 3, 0)
        layout.addWidget(self.stable_edit, 3, 1)
        layout.addWidget(unstable_label, 4, 0)
        layout.addWidget(self.unstable_edit, 4, 1)
        layout.addWidget(rect_label, 5, 0)
        layout.addWidget(self.rect_edit, 5, 1)
        layout.addWidget(duration_label, 6, 0)
        layout.addWidget(self.duration_edit, 6, 1)
        layout.addWidget(add_button, 7, 0)
        layout.addWidget(remove_button, 7, 1)
        layout.addWidget(end_label, 8, 0)
        layout.addWidget(self.end_edit, 8, 1)
        layout.addWidget(ok_btn, 9, 0)
        layout.addWidget(cancel_btn, 9, 1)
        self.edit_widget.setLayout(layout)

        self._point = None
        self.rect = None
        self._qimg = None
        self._zoom_signal.connect(vm.zoom)

        self._init_menu(vm)
        self._init_shortcut(vm)

    def _init_menu(self, vm):
        menu_bar = self.menuBar()

        file_menu = menu_bar.addMenu('文件')

        open_action = QtWidgets.QAction('打开', self)
        open_action.triggered.connect(vm.open)
        file_menu.addAction(open_action)

        file_menu.addSeparator()

        exit_action = QtWidgets.QAction('退出', self)
        exit_action.triggered.connect(QtWidgets.QApplication.quit)
        file_menu.addAction(exit_action)

    def _init_shortcut(self, vm):
        previous = QtWidgets.QAction(self)
        previous.setShortcut(QtGui.QKeySequence.MoveToPreviousChar)
        previous.triggered.connect(self.previous)

        next_ = QtWidgets.QAction(self)
        next_.setShortcut(QtGui.QKeySequence.MoveToNextChar)
        next_.triggered.connect(self.next)

        begin = QtWidgets.QAction(self)
        begin.setShortcut(QtGui.QKeySequence.fromString('F1'))
        begin.triggered.connect(vm.begin)

        stable = QtWidgets.QAction(self)
        stable.setShortcut(QtGui.QKeySequence.fromString('F2'))
        stable.triggered.connect(vm.stable)

        unstable = QtWidgets.QAction(self)
        unstable.setShortcut(QtGui.QKeySequence.fromString('F3'))
        unstable.triggered.connect(vm.unstable)

        rect = QtWidgets.QAction(self)
        rect.setShortcut(QtGui.QKeySequence.fromString('F5'))
        rect.triggered.connect(vm.rect)

        add = QtWidgets.QAction(self)
        add.setShortcut(QtGui.QKeySequence.fromString('F6'))
        add.triggered.connect(vm.add_duration)

        remove = QtWidgets.QAction(self)
        remove.setShortcut(QtGui.QKeySequence.fromString('F7'))
        remove.triggered.connect(vm.remove_duration)

        end = QtWidgets.QAction(self)
        end.setShortcut(QtGui.QKeySequence.fromString('F4'))
        end.triggered.connect(vm.end)

        esc = QtWidgets.QAction(self)
        esc.setShortcut(QtGui.QKeySequence.fromString('Esc'))
        esc.triggered.connect(self.esc)

        self.addActions([previous, next_, begin, stable, unstable, end, rect, add, remove, esc])

    @QtCore.Slot()
    def previous(self):
        value = self.scroll_bar.value()
        self.scroll_bar.setValue(value - 1)

    @QtCore.Slot()
    def next(self):
        value = self.scroll_bar.value()
        self.scroll_bar.setValue(value + 1)

    @QtCore.Slot()
    def esc(self):
        self.port_edit.clearFocus()
        self.plate_edit.clearFocus()

    def eventFilter(self, watched, event):
        def get_rect():
            p = event.l.x(), event.l.y()
            if self._point and abs(p[0] - self._point[0]) > 10 and abs(p[1] - self._point[1]) > 10:
                x = min(self._point[0], p[0])
                y = min(self._point[1], p[1])
                w = max(self._point[0], p[0]) - x
                h = max(self._point[1], p[1]) - y
                r = x, y, w, h
                self.overlay_widget.set_rect(r)
                return r
            return None

        if watched == self.touch_widget:
            if event.type() == QtCore.QEvent.MouseButtonDblClick:
                self._zoom_signal.emit(event.l.x(), event.l.y())
                return True
            if event.type() == QtCore.QEvent.MouseButtonPress:
                self._point = event.l.x(), event.l.y()
                return True
            if event.type() == QtCore.QEvent.MouseButtonRelease:
                rect = get_rect()
                if rect is not None:
                    self.rect = rect
                    self._point = None
                return True
            if event.type() == QtCore.QEvent.MouseMove:
                get_rect()
                return True
        return False
