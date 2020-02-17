from PySide2 import QtCore, QtGui, QtWidgets


class OpenDialog(QtWidgets.QFileDialog):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setFileMode(QtWidgets.QFileDialog.FileMode.Directory)
        self.setOption(QtWidgets.QFileDialog.Option.ShowDirsOnly)


class ErrorDialog(QtWidgets.QDialog):
    def __init__(self, msg, *args, **kwargs):
        super().__init__(*args, **kwargs)
        label = QtWidgets.QLabel()
        label.setText(msg)
        button = QtWidgets.QPushButton()
        button.setText('确定')
        button.clicked.connect(self.accept)
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(label)
        layout.addWidget(button)
        self.setLayout(layout)


class OverlayWidget(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._polys = []
        self._rects = []
        self._rect = None

    @property
    def polys(self):
        return self._polys

    @polys.setter
    def polys(self, polys):
        self._polys = polys
        self.update()

    @property
    def rects(self):
        return self._rects

    @rects.setter
    def rects(self, rects):
        self._rects = rects
        self.update()

    @property
    def rect(self):
        return self._rect

    @rect.setter
    def rect(self, rect):
        self._rect = rect
        self.update()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing, True)
        for poly in self._polys:
            points = [QtCore.QPoint(*p) for p in poly['points']]
            points.append(points[0])
            pen = QtGui.QPen()
            color = QtCore.Qt.red if poly['highlight'] else QtCore.Qt.green
            pen.setColor(color)
            painter.setPen(pen)
            painter.drawPolyline(points)
        for rect in self._rects:
            pen = QtGui.QPen()
            pen.setColor(QtCore.Qt.red)
            painter.setPen(pen)
            painter.drawRect(*rect)
        if self.rect:
            pen = QtGui.QPen()
            pen.setColor(QtCore.Qt.yellow)
            painter.setPen(pen)
            painter.drawRect(*self.rect)


class ImageWidget(QtWidgets.QWidget):
    _signal = QtCore.Signal(float, float)

    def __init__(self, vm, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.img_label = QtWidgets.QLabel(self)
        self.img_label.setGeometry(0, 0, 800, 600)

        self.overlay_widget = OverlayWidget(self)
        self.overlay_widget.setGeometry(0, 0, 800, 600)

        self.time_label = QtWidgets.QLabel(self)
        self.time_label.setStyleSheet('color:black;font-size:40px;background-color:white;')
        self.time_label.setGeometry(10, 10, 160, 40)

        self.touch_widget = QtWidgets.QWidget(self)
        self.touch_widget.setGeometry(0, 0, 800, 600)
        self.touch_widget.installEventFilter(self)

        self.scroll_bar = QtWidgets.QScrollBar(self)
        self.scroll_bar.setOrientation(QtCore.Qt.Orientation.Horizontal)
        self.scroll_bar.setSingleStep(1)
        self.scroll_bar.valueChanged.connect(vm.idx_update)
        self.scroll_bar.setGeometry(0, 600, 800, 20)

        self._signal.connect(vm.zoom)
        self._point = None

    def eventFilter(self, watched, event):
        def draw_rect():
            p = event.l.x(), event.l.y()
            if self._point and abs(p[0] - self._point[0]) > 10 and abs(p[1] - self._point[1]) > 10:
                x = min(self._point[0], p[0])
                y = min(self._point[1], p[1])
                w = max(self._point[0], p[0]) - x
                h = max(self._point[1], p[1]) - y
                r = x, y, w, h
                self.overlay_widget.rect = r
                return r
            return None

        if watched == self.touch_widget:
            if event.type() == QtCore.QEvent.MouseButtonDblClick:
                self._signal.emit(event.l.x(), event.l.y())
                return True
            if event.type() == QtCore.QEvent.MouseButtonPress:
                self._point = event.l.x(), event.l.y()
                return True
            if event.type() == QtCore.QEvent.MouseMove:
                draw_rect()
                return True
            if event.type() == QtCore.QEvent.MouseButtonRelease:
                if draw_rect():
                    self._point = None
                return True
        return False


class EditWidget(QtWidgets.QWidget):
    def __init__(self, vm, *args, **kwargs):
        def create_edit(title, line, placeholder, enabled):
            if line:
                edit = QtWidgets.QLineEdit()
            else:
                edit = QtWidgets.QTextEdit()
            edit.setPlaceholderText(placeholder)
            edit.setEnabled(enabled)
            layout.addRow(title, edit)
            return edit

        def create_btn(title, text1, slot1, text2, slot2):
            h_layout = QtWidgets.QHBoxLayout()
            button1 = QtWidgets.QPushButton()
            button1.setText(text1)
            button1.clicked.connect(slot1)
            h_layout.addWidget(button1)
            button2 = QtWidgets.QPushButton()
            button2.setText(text2)
            button2.clicked.connect(slot2)
            h_layout.addWidget(button2)
            layout.addRow(title, h_layout)

        super().__init__(*args, **kwargs)

        layout = QtWidgets.QFormLayout()
        self.port_edit = create_edit('泊位', True, 'Ctrl+P，跨车位用逗号分隔', True)
        self.port_edit.returnPressed.connect(self.port_edit.clearFocus)
        self.plate_edit = create_edit('车牌', True, 'Ctrl+L，双击图片可放大', True)
        self.plate_edit.returnPressed.connect(self.plate_edit.clearFocus)
        self.begin_edit = create_edit('入场时间', True, 'F1使用当前时间, 留空默认为第一张', False)
        self.stable_edit = create_edit('停稳时间', True, 'F2，留空默认为入场时间', False)
        self.unstable_edit = create_edit('移动时间', True, 'F3，留空默认为离场/下个停稳时间', False)
        self.end_edit = create_edit('离场时间', True, 'F4，留空默认为未出场', False)
        self.rect_edit = create_edit('车辆位置', True, 'F5，使用当前矩形，跨车位才需要', False)
        create_btn('停稳时段', '添加 (F6)', vm.add_duration, '删除 (F7)', vm.remove_duration)
        self.duration_edit = create_edit('已有时段', False, '只有一段或最后一段不需要添加，设置完成直接确定', False)
        self.duration_edit.setMaximumHeight(75)
        self.mode_label = QtWidgets.QLabel()
        self.mode_label.setText('添加记录')
        create_btn(self.mode_label, '确定', vm.confirm, '取消', vm.cancel)
        self.setLayout(layout)


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, vm, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle('停车记录标注')
        self.setFixedSize(1200, 800)

        self.image_widget = ImageWidget(vm, self)
        self._init_image_widget()

        self.table_widget = QtWidgets.QTableWidget(self)
        self._init_table_widget()

        self.edit_widget = EditWidget(vm, self)
        self._init_edit_widget()

        self._init_menu(vm)
        self._init_shortcut(vm)

    def _init_image_widget(self):
        self.image_widget.setHidden(True)
        self.image_widget.setGeometry(0, 23, 800, 620)

    def _init_table_widget(self):
        self.table_widget.setColumnCount(5)
        self.table_widget.setColumnWidth(0, 80)
        self.table_widget.setColumnWidth(1, 100)
        self.table_widget.setColumnWidth(2, 100)
        self.table_widget.setColumnWidth(3, 400)
        self.table_widget.setColumnWidth(4, 100)
        self.table_widget.setHorizontalHeaderLabels(['泊位', '车牌', '入场时间', '停稳时段', '离场时间'])
        self.table_widget.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.table_widget.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.table_widget.verticalHeader().setHidden(True)
        self.table_widget.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.table_widget.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.table_widget.setHidden(True)
        self.table_widget.setGeometry(0, 643, 800, 157)

    def _init_edit_widget(self):
        self.edit_widget.setHidden(True)
        self.edit_widget.setGeometry(800, 23, 400, 777)

    def _init_menu(self, vm):
        def create_action(name, key, slot):
            action = QtWidgets.QAction(name, self)
            action.setShortcut(key)
            action.triggered.connect(slot)
            return action

        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu('文件')
        open_action = create_action('打开', QtGui.QKeySequence.fromString('Ctrl+O'), vm.open)
        file_menu.addAction(open_action)
        file_menu.addSeparator()
        exit_action = create_action('退出', QtGui.QKeySequence.fromString('Alt+F4'), QtWidgets.QApplication.quit)
        file_menu.addAction(exit_action)
        record_menu = menu_bar.addMenu('记录')
        edit_action = create_action('编辑', QtGui.QKeySequence.fromString('Ctrl+E'), vm.edit_record)
        remove_action = create_action('删除', QtGui.QKeySequence.fromString('Ctrl+D'), vm.remove_record)
        record_menu.addActions([edit_action, remove_action])

    def _init_shortcut(self, vm):
        def create_action(key, slot):
            action = QtWidgets.QAction(self)
            action.setShortcut(key)
            action.triggered.connect(slot)
            return action

        left = create_action(QtGui.QKeySequence.MoveToPreviousChar, self.left)
        right = create_action(QtGui.QKeySequence.MoveToNextChar, self.right)
        up = create_action(QtGui.QKeySequence.MoveToPreviousLine, vm.up)
        down = create_action(QtGui.QKeySequence.MoveToNextLine, vm.down)
        port = create_action(QtGui.QKeySequence.fromString('Ctrl+P'), self.edit_widget.port_edit.setFocus)
        plate = create_action(QtGui.QKeySequence.fromString('Ctrl+L'), self.edit_widget.plate_edit.setFocus)
        begin = create_action(QtGui.QKeySequence.fromString('F1'), vm.begin)
        stable = create_action(QtGui.QKeySequence.fromString('F2'), vm.stable)
        unstable = create_action(QtGui.QKeySequence.fromString('F3'), vm.unstable)
        end = create_action(QtGui.QKeySequence.fromString('F4'), vm.end)
        rect = create_action(QtGui.QKeySequence.fromString('F5'), vm.rect)
        add = create_action(QtGui.QKeySequence.fromString('F6'), vm.add_duration)
        remove = create_action(QtGui.QKeySequence.fromString('F7'), vm.remove_duration)
        self.addActions([left, right, up, down, port, plate, begin, stable, unstable, end, rect, add, remove])

    @QtCore.Slot()
    def left(self):
        value = self.image_widget.scroll_bar.value()
        self.image_widget.scroll_bar.setValue(value-1)

    @QtCore.Slot()
    def right(self):
        value = self.image_widget.scroll_bar.value()
        self.image_widget.scroll_bar.setValue(value + 1)
