from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from panel.common.CommonWidgets import *


class WorkstationSimulation(QWidget):
    def __init__(self, workstation_name):
        super(WorkstationSimulation, self).__init__()
        self.workstation_name = workstation_name
        self.setWindowTitle(" ".join([self.workstation_name, "simulation configuration"]))
        self.setMinimumSize(QSize(1000, 800))
        self.users = []
        self.simulation_config = {}
        self.users_count = 0
        self.scenario_step = 0
        self.arg_count = 0

        self.create_widgets()
        self.basic_actions()
        self.show()

    def create_widgets(self):
        """ Create widgets needed for simulation configuration view:
            - QTableWidget for users
            - QTableWidget for scenarios
            - QTableWidget for args
            - Another widget for lists?

        :return: None
        :rtype: NoneType
        """
        self.users_table = QTableWidget()
        self._users_table_format()
        self.box_users_available = QComboBox()
        self.box_users_available.setEditable(True)
        self.button_add_user = QPushButton("Add user")
        self.button_remove_user = QPushButton("Remove user")
        lay = QGridLayout()
        lay.addWidget(self.box_users_available, 0, 0)
        lay.addWidget(self.button_add_user, 0, 1)
        lay.addWidget(self.button_remove_user, 0, 2)
        lay.addWidget(self.users_table, 1, 0, 2, 5)
        self.users_group = QGroupBox("Users")
        self.users_group.setLayout(lay)
        self.users_group.setMaximumWidth(600)

        self.scenarios_table = QTableWidget()
        self.scenarios_table.setMinimumWidth(600)
        self._scenarios_table_format()
        self.button_add_step = QPushButton("Add step")
        self.button_remove_step = QPushButton("Remove step")
        self.button_update_step = QPushButton("Update scenario")

        self.args_table = QTableWidget()
        self.args_table.setMinimumWidth(600)
        self._arguments_table_format()
        self.button_add_arg = QPushButton("Add argument")
        self.button_remove_arg = QPushButton("Remove argument")
        self.button_update_arg = QPushButton("Update argument")

        self.scenarios_group = QGroupBox("Scenarios")
        lay = QGridLayout()
        lay.addWidget(self.button_add_step, 0, 0)
        lay.addWidget(self.button_remove_step, 0, 1)
        lay.addWidget(self.button_update_step, 0, 2)
        lay.addWidget(self.scenarios_table, 1, 0, 2, 3)

        lay.addWidget(self.button_add_arg, 0, 4)
        lay.addWidget(self.button_remove_arg, 0, 5)
        lay.addWidget(self.button_update_arg, 0, 6)
        lay.addWidget(self.args_table, 1, 4, 2, 3)
        self.scenarios_group.setLayout(lay)

        lay = QHBoxLayout()
        lay.addWidget(self.users_group)
        lay.addWidget(self.scenarios_group)
        self.setLayout(lay)

    def basic_actions(self):
        """ Connects widgets signals to slot functions

        :return: None
        """
        self.button_add_user.clicked.connect(self.add_user)
        self.button_remove_user.clicked.connect(self.remove_user)

        self.button_add_step.clicked.connect(self.add_step)
        self.button_remove_step.clicked.connect(self.remove_step)

        self.button_add_arg.clicked.connect(self.add_argument)
        self.button_remove_arg.clicked.connect(self.remove_argument)

        self.users_table.itemSelectionChanged.connect(self.show_steps)
        self.scenarios_table.itemSelectionChanged.connect(self.show_arg)
        self.button_update_step.clicked.connect(self.update_steps)
        self.button_update_arg.clicked.connect(self.update_arg)

    ##################################################################
    # MANAGING USERS LIST
    ##################################################################
    @pyqtSlot()
    def add_user(self):
        """ Add an element to users list and update view

        :return: None
        """
        # Get currently selected user
        username = self.box_users_available.currentText()
        # Add user to users list
        if username not in self.users and username not in [""]:
            self.users.append(username)
            self.simulation_config[username] = []
            self.show_users_list()
        else:
            PopUpWidget("Same username cannot be used twice")
        res = self.box_users_available.findText(username)
        if res == -1:
            self.box_users_available.addItem(username)

    @pyqtSlot()
    def remove_user(self):
        """ Remove selected user from users list and update view

        :return: None
        """
        # Selecting username index to delete
        try:
            selected_index = self.users_table.currentRow()
            self.simulation_config.pop(self.users[selected_index])
            self.users.pop(selected_index)  # Remove configuration set for deleted user
            self.show_users_list()
        except:
            PopUpWidget("No user has been selected")

    def show_users_list(self):
        """ Function used to update users table view

        :return: None
        """
        self._clear_users_table()
        self._users_table_format()
        row_count = len(self.users)
        for row_index in range(row_count):
            user = QLineEdit(self.users[row_index])
            user.setReadOnly(True)
            self.users_table.insertRow(row_index)
            self.users_table.setCellWidget(row_index, 0, user)

    def get_selected_user_in_table(self):
        """ Get selected user index

        :return: User index
        :rtype: int
        """
        try:
            user = self.users_table.currentRow()
        except:
            user = -1
        return user

    def get_selected_username(self):
        """ Get selected user name

        :return: User name
        :rtype: str
        """
        try:
            username = self.users_table.cellWidget(self.get_selected_user_in_table(), 0).text()
        except:
            username = ""
        return username

    ############################################################################
    # MANAGING SCENARIO STEPS
    ############################################################################
    @pyqtSlot()
    def add_step(self):
        """ Add a scenario step to specific key in simulation collection

        :return: None
        """
        username = self.get_selected_username()
        if username in self.simulation_config.keys():
            self.simulation_config[username].append(self._create_scenario_step())
        self.show_steps()

    @pyqtSlot()
    def remove_step(self):
        """ Remove selected step in scenario collection for specific user

        :return: None
        """
        try:
            selected_index = self.scenarios_table.currentRow()
        except:
            PopUpWidget("No simulation step has been selected")
            return

        username = self.get_selected_username()
        if username in self.simulation_config.keys():
            try:
                self.simulation_config[username].pop(selected_index)
                self.show_steps()
            except:
                pass

    def show_steps(self):
        """ Updates scenario steps view

        :return: None
        """
        self._clear_scenarios_table()
        self._scenarios_table_format()

        username = self.get_selected_username()
        if username in self.simulation_config.keys():
            # for each dictionary in self.simulation_config[username], add line with data
            for simulation_step in range(len(self.simulation_config[username])):
                self._show_step(simulation_step, username)

    def _show_step(self, step, username):
        """ Create widgets for each step in scenario

        :param step: index of simulation values
        :type step: int
        :param username: username, key in config_simulation dict
        :type username: str
        :return:
        """
        # Check if simulation step is an empty dict
        d_to_check = self.simulation_config[username][step]
        self.scenarios_table.insertRow(step)
        if d_to_check != {}:
            if "name" in d_to_check.keys():
                name = QLineEdit(d_to_check["name"])
            else:
                name = QLineEdit("")
            self.scenarios_table.setCellWidget(step, 0, name)

            if "rep" in d_to_check.keys():
                rep = QLineEdit(d_to_check["rep"])
            else:
                rep = QLineEdit("")
            self.scenarios_table.setCellWidget(step, 1, rep)

            if "begin" in d_to_check.keys():
                begin = QLineEdit(d_to_check["begin"])
            else:
                begin = QLineEdit("")
            self.scenarios_table.setCellWidget(step, 2, begin)

    @pyqtSlot()
    def update_steps(self):
        try:
            username = self.get_selected_username()
        except:
            return

        for index in range(self.scenarios_table.rowCount()):
            if username in self.simulation_config.keys():
                self.simulation_config[username][index]["name"] = self.scenarios_table.cellWidget(index, 0).text()
                self.simulation_config[username][index]["rep"] = self.scenarios_table.cellWidget(index, 1).text()
                self.simulation_config[username][index]["begin"] = self.scenarios_table.cellWidget(index, 2).text()

    @pyqtSlot()
    def add_argument(self):
        """ Add a new line in arguments table widget

        :return: None
        """
        try:
            index = self.scenarios_table.currentRow()
        except:
            PopUpWidget("No simulation step selected")
            return

        newLine = self.args_table.rowCount()
        self.args_table.insertRow(newLine)
        self.args_table.setCellWidget(newLine, 0, QLineEdit(""))
        self.args_table.setCellWidget(newLine, 1, QLineEdit(""))

    @pyqtSlot()
    def remove_argument(self):
        """ Removes selected line in argument table widget

        :return: None
        """
        try:
            step_index = self.scenarios_table.currentRow()
        except:
            PopUpWidget("No step selected")
            return

        try:
            arg_index = self.args_table.currentRow()
            arg_key = self.args_table.cellWidget(arg_index, 0).text()
        except:
            PopUpWidget("No argument selected")
            return

        username = self.get_selected_username()
        if username in self.simulation_config.keys() :
            try:
                self.scenarios_table[username][step_index]["args"].pop(arg_key)
            except KeyError:
                pass
        self.show_arg()

    @pyqtSlot()
    def update_arg(self):
        """ Apply currently set values on HMI on configuration collection

        :return:
        """
        # Get username
        username = self.get_selected_username()
        if username not in self.simulation_config.keys():
            return
        # Get simulation step
        try:
            step_index = self.scenarios_table.currentRow()
        except:
            return
        # Update data in config collection
        arg_dict = {}
        for index in range(self.args_table.rowCount()):
            arg_name = self.args_table.cellWidget(index, 0).text()
            try:
                arg_value = self.self.args_table.cellWidget(index, 1).get_configuration()
            except:
                arg_value = self.args_table.cellWidget(index, 1).text()
            arg_dict[arg_name] = arg_value

        self.simulation_config[username][step_index]["args"].update(arg_dict)

    def show_arg(self):
        """ Update view in argument table widget

        :return: None
        """
        self._clear_arguments_table()
        self._arguments_table_format()
        username = self.get_selected_username()
        if username not in self.simulation_config.keys():
            return
        try:
            step_index = self.scenarios_table.currentRow()
        except:
            return
        # Update view
        try:
            row_index = 0
            to_show = self.simulation_config[username][step_index]["args"]
            if to_show != {}:
                for key, value in to_show.items():
                    self.args_table.insertRow(row_index)
                    self.args_table.setCellWidget(row_index, 0, QLineEdit(key))
                    # When loading config, values sometimes have not same type
                    if type(value) not in [list, dict]:
                        self.args_table.setCellWidget(row_index, 1, QLineEdit(value))
                    elif type(value) in [list]:
                        law = ListArgumentWidget(value)
                        law.set_configuration()
                        self.args_table.setCellWidget(row_index, 1, law)

                    elif type(value) in [dict]:
                        daw = DictArgumentWidget(value)
                        daw.set_configuration()
                        self.args_table.setCellWidget(row_index, 1, daw)
                    row_index += 1
        except:
            pass

    def set_users(self, users_list):
        self.box_users_available.addItems(users_list)

    def set_configuration(self, sim_config):
        """ Set configuration data in corresponding widgets

        :param sim_config: Simulation configuration
        :type sim_config: list
        :return: None
        :rtype: NoneType
        """
        self.users = [elt["name"] for elt in sim_config]
        self.box_users_available.addItems(self.users)
        self.simulation_config = {elt["name"]: elt["scenarios"] for elt in sim_config}
        self.show_users_list()
        self.show_steps()
        self.show_arg()

    def get_configuration(self):
        """ Reformat configuration in order to generate conf_sim.json

        :return:
        """
        users = []
        for username, config in self.simulation_config.items():
            user_config = {
                "name": username,
                "scenarios": config
            }
            users.append(user_config)
        workstation_config = {
            "hostname": self.workstation_name,
            "users": users
        }
        return workstation_config

    def _create_scenario_step(self):
        """ Basic object used a scenario step

        :return:
        """
        scen_step = {
            "name": "",
            "rep": "",
            "begin": "",
            "args": {}
        }
        return scen_step

    #######################################################################
    def _clear_users_table(self):
        """ Clean user table widget

        :return: None
        """
        self.users_table.clear()
        self.users_table.setRowCount(0)
        self.users_table.setColumnCount(0)

    def _users_table_format(self):
        """ Set header in user table widget

        :return: None
        """
        self.users_table.insertColumn(0)
        self.users_table.columnWidth(250)
        self.users_table.setHorizontalHeaderLabels(["Users"])

    def _clear_scenarios_table(self):
        """ Clean scenario table widget

        :return: None
        """
        self.scenarios_table.clear()
        self.scenarios_table.setRowCount(0)
        self.scenarios_table.setColumnCount(0)

    def _scenarios_table_format(self):
        """ Set header in scenario table widget

        :return: None
        """
        self.scenarios_table.insertColumn(0)
        self.scenarios_table.insertColumn(1)
        self.scenarios_table.insertColumn(2)
        self.scenarios_table.setHorizontalHeaderLabels(["Name", "Rep", "Begin at step"])

    def _clear_arguments_table(self):
        """ Clean argument table widget

        :return: None
        """
        self.args_table.clear()
        self.args_table.setRowCount(0)
        self.args_table.setColumnCount(0)

    def _arguments_table_format(self):
        """ Set header in argument table widget

        :return: None
        """
        self.args_table.insertColumn(0)
        self.args_table.insertColumn(1)
        self.args_table.columnWidth(350)
        self.args_table.setHorizontalHeaderLabels(["Name", "Value"])
