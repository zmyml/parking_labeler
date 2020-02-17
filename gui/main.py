from gui.view_model import ViewModel
from PySide2 import QtWidgets


def main():
    app = QtWidgets.QApplication()
    vm = ViewModel()
    vm.main_win.show()
    app.exec_()


if __name__ == '__main__':
    main()
