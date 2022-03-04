# QT
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QSize


class PopUpWidget(QMessageBox):
    def __init__(self, message):
        """ Generic QMessageBox """
        super(PopUpWidget, self).__init__()
        self.setWindowTitle("SI Simulator")
        self.setText(message)
        self.exec()


class ArgumentWidget(QWidget):
    def __init__(self):
        super(ArgumentWidget, self).__init__()
        self.create_widgets()
        self.set_layout()
        self.basic_actions()
        self.hide()

    def create_widgets(self):
        """ Creating widgets required for visualisation"""
        self.add_arg = QPushButton("+")
        self.remove_arg = QPushButton("-")
        self.table_argument = QTableWidget()

    def set_layout(self):
        """ Set layout """
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.add_arg, 0, 0)
        grid_layout.addWidget(self.remove_arg, 0, 1)
        grid_layout.addWidget(self.table_argument, 1, 0, 2, 2)
        self.setLayout(grid_layout)

    def basic_actions(self):
        """ Connects signals to slot functions """
        self.add_arg.clicked.connect(self.add_argument)
        self.remove_arg.clicked.connect(self.remove_argument)

    def add_argument(self):
        """ Insert row in table widget """
        self.table_argument.insertRow(self.table_argument.rowCount())

    def remove_argument(self):
        """ Remove row in table widget"""
        try:
            self.table_argument.removeRow(self.table_argument.currentRow())
        except:
            PopUpWidget("No item selected")

    def set_format_table(self):
        """ Set header to table widget, must be overridden"""
        pass

    def set_configuration(self):
        """ Set data to table widget, must be overridden """
        pass

    def get_configuration(self):
        """ Get data from table widget, must be overridden """
        pass


class DictArgumentWidget(ArgumentWidget):
    def __init__(self, arg_dict):
        """ Class inheriting of ArgumentWidget in order to show arguments which type is dict

        :param arg_dict: Argument values
        :type arg_dict: dict
        """
        super(DictArgumentWidget, self).__init__()
        self.set_format_table()
        self.arg = arg_dict

    def set_configuration(self):
        iter = 0
        for key, value in self.arg.items():
            self.table_argument.insertRow(iter)
            self.table_argument.setItem(iter, 0, QTableWidgetItem(key))
            self.table_argument.setItem(iter, 1, QTableWidgetItem(value))
            iter += 1

    def get_configuration(self):
        config = {}
        for index in range(self.table_argument.rowCount()):
            config[self.table_argument.item(index, 0).text()] = self.table_argument.item(index, 1).text()
        return config

    def set_format_table(self):
        self.table_argument.insertColumn(0)
        self.table_argument.insertColumn(1)
        self.table_argument.setHorizontalHeaderLabels(["Argument", "Value"])


class ListArgumentWidget(ArgumentWidget):
    def __init__(self, arg_list):
        """ Class inheriting of ArgumentWidget in order to show arguments which type is list

        :param arg_list: Argument values
        :type arg_list: list
        """
        super(ListArgumentWidget, self).__init__()
        self.set_format_table()
        self.arg = arg_list

    def set_configuration(self):
        iter = 0
        for value in self.arg:
            self.table_argument.insertRow(iter)
            self.table_argument.setItem(iter, 0, QTableWidgetItem(value))
            iter += 1

    def get_configuration(self):
        config = []
        for index in range(self.table_argument.rowCount()):
            config.append(self.table_argument.item(index, 0).text())
        return config

    def set_format_table(self):
        self.table_argument.insertColumn(0)
        self.table_argument.setHorizontalHeaderLabels(["Value"])


def openConfigFile(title=None):
    """ Generic File Dialog """
    # TODO: Check how to set title to QFileDialog
    dial = QFileDialog()
    if title is not None:
        dial.setWindowTitle(title)
    dial.setBaseSize(QSize(1480, 900))
    dial.setAcceptMode(dial.AcceptMode(1))
    file = dial.getOpenFileName(options=QFileDialog.DontUseNativeDialog)[0]
    return file