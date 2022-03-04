from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from common.config import Config, workstation_methods
from panel.common.CommonWidgets import *


class WorkstationConfiguration(QWidget):
    def __init__(self, workstation_name, workstation_type):
        super(WorkstationConfiguration, self).__init__()
        self.workstation_name = workstation_name
        self.workstation_type = workstation_type

        self.resize(QSize(1600, 500))
        self.create_widgets()
        self.item_count = 0

        self._configuration = {}
        self.networks_available = []

        self.basic_actions()

    def create_widgets(self):
        # Labels
        self.name_label = QLabel("Workstation name")
        self.distribution_label = QLabel("Distribution")
        self.release_label = QLabel("Release")
        self.network_name_label = QLabel("Network name")
        self.network_interface_label = QLabel("Network interface")
        self.network_ip_label = QLabel("IP address")
        self.network_subnet_label = QLabel("Subnet")
        self.gateway_label = QLabel("Gateway")
        self.camera_label = QCheckBox("Camera")

        # Line Edits
        self.name_value = QLabel(self.workstation_name)
        self.distribution_value = QLineEdit()
        self.distribution_value.setText("ubuntu")
        self.release_value = QLineEdit()
        self.release_value.setText("bionic")
        self.network_value = QComboBox()
        self.interface_value = QLineEdit()
        self.interface_value.setText("eth1")
        self.ip_value = QLineEdit()
        self.ip_value.setText("10.122.0.")
        self.subnet_value = QLineEdit()
        self.subnet_value.setText("24")
        self.gateway_value = QLineEdit()
        self.gateway_value.setText("10.122.0.1")

        # Group box
        self.group_box = QGroupBox(self)
        self.group_box.setTitle(self.workstation_name + ' physic configuration')
        # Grid layout
        self.grid_layout = QGridLayout()
        # Workstation name
        self.grid_layout.addWidget(self.name_label, 0, 0)
        self.grid_layout.addWidget(self.name_value, 0, 1)
        # Distribution name
        self.grid_layout.addWidget(self.distribution_label, 0, 3)
        self.grid_layout.addWidget(self.distribution_value, 0, 4)
        # Release name
        self.grid_layout.addWidget(self.release_label, 0, 6)
        self.grid_layout.addWidget(self.release_value, 0, 7)
        # Network name
        self.grid_layout.addWidget(self.network_name_label, 1, 0)
        self.grid_layout.addWidget(self.network_value, 1, 1)
        # Interface name
        self.grid_layout.addWidget(self.network_interface_label, 1, 3)
        self.grid_layout.addWidget(self.interface_value, 1, 4)
        # IP address
        self.grid_layout.addWidget(self.network_ip_label, 1, 6)
        self.grid_layout.addWidget(self.ip_value, 1, 7)
        # Subnet
        self.grid_layout.addWidget(self.network_subnet_label, 2, 0)
        self.grid_layout.addWidget(self.subnet_value, 2, 1)
        # Gateway
        self.grid_layout.addWidget(self.gateway_label, 2, 3)
        self.grid_layout.addWidget(self.gateway_value, 2, 4)
        #Camera
        self.grid_layout.addWidget(self.camera_label, 2, 6, 1, 2)

        self.group_box.setLayout(self.grid_layout)

    def update_networks_list(self, networks_list):
        # Get current network name
        former_network = self.network_value.currentText()
        # Clean combo box
        self.network_value.clear()
        self.network_value.addItem("")
        # Recreate networks list
        for network in networks_list:
            # item network is a dict
            self.network_value.addItem(network["name"])
        self.network_value.addItem("lxdbr0")
        # If selected network has not been removed, set index to combo box
        former_index = self.network_value.findText(former_network)
        self.network_value.setCurrentIndex(former_index)
        self.networks_available = networks_list

    def set_configuration(self, config):
        """ Set data stored in config to widgets available in view

        :param config: Parameters to be set
        :type config: dict
        :return: None
        """
        self.name_value.setText(config["hostname"])
        self.distribution_value.setText(config["distribution"])
        self.release_value.setText(config["release"])
        network_index = self.network_value.findText(config["networks"][0]["name"])
        self.network_value.setCurrentIndex(network_index)
        self.interface_value.setText(config["networks"][0]["interface"])
        self.ip_value.setText(config["networks"][0]["ip_v4"])
        self.subnet_value.setText(config["networks"][0]["subnet"])
        self.gateway_value.setText(config["gateway"])
        self.camera_label.setChecked(config["camera"] in ["true"])

    def get_current_configuration(self):
        """ Read data entered in editable fields

        :return: Currently set configuration
        :rtype: dict
        """
        self._configuration = {
            "hostname": self.name_value.text(),
            "distribution": self.distribution_value.text(),
            "release": self.release_value.text(),
            "network_name": self.network_value.currentText(),
            "network_interface": self.interface_value.text(),
            "ip_address": self.ip_value.text(),
            "subnet": self.subnet_value.text(),
            "gateway": self.gateway_value.text(),
            "camera": str(self.camera_label.isChecked()).lower()
        }
        return self._configuration

    def basic_actions(self):
        """ Connects signals to dedicated functions """
        self.network_value.currentTextChanged.connect(self.update_network_values)

    @pyqtSlot()
    def update_network_values(self):
        """ Regarding selected network, set values to widgets """
        # Find selected network
        current_network_name = self.network_value.currentText()
        if current_network_name not in ["", "lxdbr0"]:
            current_network = next(network for network in self.networks_available if network["name"] == current_network_name)
            base_ip = ".".join(current_network["ip_v4"].split(".")[0:-1])
            subnet = current_network["subnet"]
            gateway = ".".join([base_ip, "1"])
            # Then, set values to required widgets
            current_ip = self.ip_value.text().split(".")[-1]
            self.ip_value.setText(base_ip + "." + current_ip)
            self.subnet_value.setText(subnet)
            self.gateway_value.setText(gateway)
            if "interface" in current_network.keys():
                self.interface_value.setText(current_network["interface"])
        if current_network_name in ["lxdbr0"]:
            self.ip_value.setText("default_ip_on_lxdbr0")
            self.subnet_value.setText("24")
            self.gateway_value.setText("default_gateway_on_lxdbr0")
            self.interface_value.setText("")

    def check_values(self):
        """ Check if entered values are as expected

        :return: Collection of bool related to value checking
        :rtype: dict
        """
        dist = True if self.distribution_value.text() in ["ubuntu", "debian"] else False
        network = True if self.network_value.currentText() not in [""] else False
        split_ip = self.ip_value.text().split(".")
        ip = True if split_ip[-1] not in [""] else False
        gateway = True if split_ip[-1] not in [""] else False

        assertion = {
            "distribution": dist,  # if wrong distribution set
            "network": network,  # if wrong network name set
            "ip": ip,  # if ip address is incomplete,
            "gateway": gateway  # if gateway is incomplete
        }

        return assertion


class WorkstationActions(QWidget):

    def __init__(self, workstation_name, workstation_type):
        super(WorkstationActions, self).__init__()
        self.workstation_name = workstation_name
        self.workstation_type = workstation_type

        self._workstations_actions = {}
        self.users_available = []
        self.retrieve_workstations_actions()

        self.create_widgets()
        self.set_layout()
        self.create_actions_list(self.workstation_type)
        self.basic_actions()

        # Counters
        self.item_count = 0  # for actions
        self.parameter_count = 0  # for arguments

        # Dictionary to store set actions
        self._actions_list = []

    def retrieve_workstations_actions(self):
        """ Loads functions defined in logic_actions scripts """
        self._workstations_actions["workstation"] = []
        _workstations = [w for w in Config.get_available_workstations() if w not in ["workstation"]]
        # For each type of workstation, get dedicated actions and utils actions
        for workstation in _workstations:
            self._workstations_actions[workstation] = workstation_methods[workstation]()
            self._workstations_actions[workstation] += workstation_methods["utils"]()
            self._workstations_actions["workstation"] += self._workstations_actions[workstation]
        # common_actions = [actions.items() for workstation, actions in self._workstations_actions.items()]
        self._workstations_actions["workstation"] += Config.get_workstations_methods()
        self._workstations_actions["workstation"] += workstation_methods["utils"]()

    def basic_actions(self):
        """ Connects signals to dedicated functions """
        # Actions
        self.actions_apply.clicked.connect(self.add_action)
        self.remove_button.clicked.connect(self.remove_action)
        # Parameters
        self.add_param_button.clicked.connect(self.add_parameter)
        self.remove_param_button.clicked.connect(self.remove_parameter)
        # Table actions
        self.reset_button.clicked.connect(self.reset_tables)
        self.default_button.clicked.connect(self.default_configuration)
        self.up_button.clicked.connect(self.item_up)
        self.down_button.clicked.connect(self.item_down)
        self.apply_parameters.clicked.connect(self.update_parameter_table)
        # Qt signals
        self.actions_table.itemSelectionChanged.connect(self.generate_parameter_table)

    @pyqtSlot()
    def add_action(self):
        """ Add an element to the actions table widget """
        try:
            act = self.actions_table.currentRow()
            name = self.actions_list.currentText()
            if name not in [""]:
                d_actions = {"name": self.actions_list.currentText()}
            else:
                return
            self._actions_list.append(d_actions)
            # self._actions_arg.append(self.actions_args.text())
            self.generate_action_table()
        except:
            print("No item selected")

    @pyqtSlot()
    def remove_action(self):
        """ Remove an element from actions table widget """
        try:
            item_index = self.actions_table.currentRow()
            self._actions_list.pop(item_index)
            self.generate_action_table()
        except:
            print("No item selected")

    def generate_action_table(self):
        """ Generates actions table using data stored in _actions_list """
        # Create item to add action to QTableWidget
        self.item_count = 0
        self.actions_table.clear()
        self.actions_table.setRowCount(0)
        self.actions_table.setHorizontalHeaderLabels(["Actions"])
        for index in range(len(self._actions_list)):
            action_label = QTableWidgetItem(self._actions_list[index]["name"])
            # action_arg = QTableWidgetItem(self._actions_arg[index])
            self.actions_table.insertRow(self.item_count)
            self.actions_table.setItem(self.item_count, 0, action_label)
            # self.actions_table.setItem(self.item_count, 1, action_arg)
            self.item_count += 1

    @pyqtSlot()
    def add_parameter(self):
        """ Add an empty line to parameters table widget """
        # Get action name
        try:
            param_name = QComboBox()
            param_name.setEditable(True)
            param_name.addItem("")
            action_name = self.actions_table.item(self.actions_table.currentRow(), 0).text()
            for elt in Config.get_authorized_values(action_name):
                param_name.addItem(elt)
            parameter_value = QLineEdit("")
            self.complex_actions_table.insertRow(self.parameter_count)

            # Add widgets to each line of parameters table
            self.complex_actions_table.setCellWidget(self.parameter_count, 0, param_name)
            self.complex_actions_table.setCellWidget(self.parameter_count, 1, parameter_value)
            self.parameter_count += 1
        except:
            pass

    @pyqtSlot()
    def remove_parameter(self):
        """ Removes selected element from parameters table """
        try:
            # Get selected action index
            action_index = self.actions_table.currentRow()
            # Get selected parameter name
            parameter = self.complex_actions_table.cellWidget(self.complex_actions_table.currentRow(), 0).currentText()
            self.complex_actions_table.removeRow(self.complex_actions_table.currentRow())
            # Remove selected parameter from _actions_list (containing configuration)
            if parameter in self._actions_list[action_index]["args"].keys():
                self._actions_list[action_index]["args"].pop(parameter)
                self.generate_parameter_table()
        except:
            pass

    @pyqtSlot()
    def update_parameter_table(self):
        """ Set up current action configuration as new configuration """
        d_args = {}
        try:
            # Get current action index and name
            action_index = self.actions_table.currentRow()
            action_name = self.actions_table.item(action_index, 0).text()
            # Get data in parameters table and set it in d_args
            for index in range(self.complex_actions_table.rowCount()):
                param_name = self.complex_actions_table.cellWidget(index, 0).currentText()
                try:
                    param_value = self.complex_actions_table.cellWidget(index, 1).get_configuration()
                except:
                    param_value = self.complex_actions_table.cellWidget(index, 1).text()
                ##########################################################################
                # Get availables users
                ##########################################################################
                if param_name in ["create_sim_user"]:
                    self.users_available.append(param_value)
                d_args[param_name] = param_value
            # once d_args if filled with all parameters, it is stored in an object used in json file generation
            d_complete = {
                "name": action_name,
                "args": d_args
            }
            self._actions_list[action_index] = d_complete
            self.generate_parameter_table()
        except:
            pass

    @pyqtSlot()
    def generate_parameter_table(self):
        """ Updates parameter table view """
        # Clear table
        self.parameter_count = 0
        self.complex_actions_table.clear()
        self.complex_actions_table.setRowCount(0)
        self.complex_actions_table.setHorizontalHeaderLabels(["Parameters", "Values"])
        try:
            # Get action index
            action_index = self.actions_table.currentRow()
            self.parameter_count = 0
            # Show values
            for action, argument in self._actions_list[action_index]["args"].items():
                param_name = QComboBox()
                param_name.setEditable(True)
                param_name.addItem("")
                for elt in Config.get_authorized_values(self._actions_list[action_index]["name"]):
                    param_name.addItem(elt)
                param_name.setCurrentText(action)
                if type(argument) not in [dict, list]:
                    parameter_value = QTextEdit(argument)
                elif type(argument) is list:
                    parameter_value = ListArgumentWidget(argument)
                    parameter_value.set_configuration()
                elif type(argument) is dict:
                    parameter_value = DictArgumentWidget(argument)
                    parameter_value.set_configuration()
                else:
                    parameter_value = QTextEdit("Must be checked in json file")

                self.complex_actions_table.insertRow(self.parameter_count)
                self.complex_actions_table.setCellWidget(self.parameter_count, 0, param_name)
                self.complex_actions_table.setCellWidget(self.parameter_count, 1, parameter_value)
                self.parameter_count += 1
        except:
            pass

    @pyqtSlot()
    def reset_tables(self):
        """ Clears all values set in QTableWidgets

        :return: None
        """
        self.actions_table.clear()
        self.actions_table.setRowCount(0)
        self.actions_table.setHorizontalHeaderLabels(["Actions"])
        self.complex_actions_table.clear()
        self.complex_actions_table.setRowCount(0)
        self.complex_actions_table.setHorizontalHeaderLabels(["Parameters", "Values"])
        self._actions_list = []

    @pyqtSlot()
    def default_configuration(self):
        pass

    @pyqtSlot()
    def item_up(self):
        """ Change actions table order

        :return: None
        """
        try:
            current_index = self.actions_table.currentRow()
            if current_index == 0:
                return
            if current_index >= 1:
                self._actions_list[current_index - 1], self._actions_list[current_index] = self._actions_list[current_index], self._actions_list[current_index - 1]
            self.generate_action_table()
            self.generate_parameter_table()
        except:
            pass

    @pyqtSlot()
    def item_down(self):
        """ Change actions table order

        :return: None
        """
        try:
            current_index = self.actions_table.currentRow()
            if current_index == self.actions_table.rowCount():
                return
            if current_index <= self.actions_table.rowCount() - 1:
                self._actions_list[current_index + 1], self._actions_list[current_index] = self._actions_list[current_index], self._actions_list[current_index + 1]
            self.generate_action_table()
            self.generate_parameter_table()
        except:
            pass

    def create_actions_list(self, workstation_type):
        """ Loads functions defined in logic_actions scripts and set up in available actions

        :param workstation_type: Current workstation type
        :type workstation_type: str
        :return: None
        """
        if workstation_type in self._workstations_actions.keys():
            # Concatenate specific workstation actions and common actions
            available_actions = list(set(self._workstations_actions[workstation_type]))
        else:
            available_actions = list(set(self._workstations_actions["workstation"]))
        # Set availables actions to QComboBox
        self.actions_list.addItems(available_actions)

    def create_widgets(self):
        # Selecting actions to add
        self.actions_label = QLabel("Actions: ")
        self.actions_list = QComboBox()  # Box containing available actions
        self.actions_list.addItem("")
        self.actions_list.setEditable(True)
        self.actions_apply = QPushButton("Add action")

        # Then, a table is needed to show applied functions
        self.actions_table = QTableWidget()
        self.actions_table.insertColumn(0)
        self.actions_table.setColumnWidth(0, 450)
        self.actions_table.setHorizontalHeaderLabels(["Actions"])

        # Then another table is required for more complex actions
        self.complex_actions_table = QTableWidget()
        self.complex_actions_table.insertColumn(0)
        self.complex_actions_table.setColumnWidth(0, 300)
        self.complex_actions_table.insertColumn(1)
        self.complex_actions_table.setColumnWidth(1, 600)
        self.complex_actions_table.setHorizontalHeaderLabels(["Parameters", "Values"])

        # With button actions
        self.up_button = QPushButton("Up")
        self.down_button = QPushButton("Down")
        self.remove_button = QPushButton("Remove action")
        self.default_button = QPushButton("Default configuration")
        self.reset_button = QPushButton("Reset configuration")
        self.add_param_button = QPushButton("+")
        self.remove_param_button = QPushButton("-")
        self.apply_parameters = QPushButton("Update configuration")

    def set_layout(self):
        # Main layout
        self.main_layout = QVBoxLayout(self)
        # Header
        self.header = QGroupBox("logic configuration")
        logic_layout = QHBoxLayout()
        #Config actions
        actions = QGroupBox()
        actions.setMaximumWidth(800)
        actions_layout = QGridLayout()
        actions_layout.addWidget(self.actions_label, 0, 0)
        actions_layout.addWidget(self.actions_list, 0, 1, 1, 2)
        actions_layout.addWidget(self.actions_apply, 1, 0)
        actions_layout.addWidget(self.remove_button, 1, 1)

        actions_layout.addWidget(self.up_button, 3, 2)
        actions_layout.addWidget(self.down_button, 4, 2)
        actions_layout.addWidget(self.reset_button, 8, 2)

        actions_layout.addWidget(self.actions_table, 3, 0, 6, 2)

        actions.setLayout(actions_layout)

        args = QGroupBox()
        args_layout = QGridLayout()
        args_layout.addWidget(self.add_param_button, 0, 0)
        args_layout.addWidget(self.remove_param_button, 0, 1)
        args_layout.addWidget(self.complex_actions_table, 1, 0, 6, 2)
        args_layout.addWidget(self.apply_parameters, 8, 0, 1, 2)
        args.setLayout(args_layout)

        logic_layout.addWidget(actions)
        logic_layout.addWidget(args)
        self.header.setLayout(logic_layout)
        self.main_layout.addWidget(self.header)

    def set_configuration(self, d_actions):
        """ Set data loaded by reading json file to class object

        :param d_actions: Values loaded
        :type d_actions: dict
        :return:
        """
        self._actions_list = d_actions
        self.generate_action_table()

    def get_current_actions(self):
        """ Get data available in interface

        :return: Formatted data
        :rtype: dict
        """
        return {self.workstation_name: self._actions_list}

    def get_available_users(self):
        """ Get configured users available

        :return: List of users
        :rtype: list
        """
        return self.users_available

    def check_values(self):
        pass
