from PyQt5.QtCore import *
from PyQt5.QtWidgets import *


class NetworksConfiguration(QWidget):
    def __init__(self):
        super(NetworksConfiguration, self).__init__()
        self.workstation_name = "networks"
        # self.resize(QSize(1000, 500))
        # self.setMinimumSize(1600, 500)
        # self.setMaximumSize(1600, 500)
        self.create_network_widget()
        self.network_actions()
        self.item_count = 0
        self._networks_list = []
        self._configuration = {}

    def create_network_widget(self):
        self.vertical = QVBoxLayout(self)
        # First network
        # # Labels
        network_name_label = QLabel("Network name")
        network_subnet_label = QLabel("Subnet")
        network_driver_label = QLabel("Network driver")

        # # Line edit
        # # # Eth
        self.network_name_value = QLineEdit()
        self.subnet_value = QLineEdit()
        self.subnet_value.setText("10.122.0.254/24")
        self.driver_value = QLineEdit()
        self.driver_value.setText("bridge")
        self.add_network = QPushButton("Add network")
        self.remove_network = QPushButton("Remove network")
        # QTableWidget
        self.networks_table = QTableWidget()
        self.networks_table.insertColumn(0)
        self.networks_table.setColumnWidth(0, 500)
        self.networks_table.insertColumn(1)
        self.networks_table.setColumnWidth(1, 500)
        self.networks_table.insertColumn(2)
        self.networks_table.setColumnWidth(2, 400)
        self.networks_table.setHorizontalHeaderLabels(["Network name", "Subnet", "Driver"])

        # Group box
        self.group_box_network = QGroupBox()
        self.group_box_network.setTitle("Network configuration")
        # Grid layout
        self.grid_layout = QGridLayout()
        # Network name
        self.grid_layout.addWidget(network_name_label, 0, 0)
        self.grid_layout.addWidget(self.network_name_value, 0, 1)
        # network driver
        self.grid_layout.addWidget(network_driver_label, 0, 3)
        self.grid_layout.addWidget(self.driver_value, 0, 4)
        # Subnet
        self.grid_layout.addWidget(network_subnet_label, 1, 0)
        self.grid_layout.addWidget(self.subnet_value, 1, 1)
        # Add network
        self.grid_layout.addWidget(self.add_network, 1, 3)
        self.grid_layout.addWidget(self.remove_network, 1, 4)

        # Networks table
        self.grid_layout.addWidget(self.networks_table, 2, 0, 2, 5)
        # Set layout
        self.group_box_network.setLayout(self.grid_layout)

        self.vertical.addWidget(self.group_box_network)
        # self.vertical.addWidget(self.group_box_network2)

    def network_actions(self):
        self.add_network.clicked.connect(self.add_network_configuration)
        self.remove_network.clicked.connect(self.remove_network_configuration)

    @pyqtSlot()
    def add_network_configuration(self):
        network_name = self.network_name_value.text()
        network_subnet = self.subnet_value.text().split("/")
        network_driver = self.driver_value.text()

        network_config = {
            "name": network_name,
            "ip_v4": network_subnet[0],
            "subnet": network_subnet[1],
            "driver": network_driver
        }
        self._networks_list.append(network_config)
        self.generate_networks_list()

    @pyqtSlot()
    def remove_network_configuration(self):
        try:
            index_to_remove = self.networks_table.currentRow()
            self._networks_list.pop(index_to_remove)
            self.generate_networks_list()
        except:
            pass

    def generate_networks_list(self):
        self.item_count = 0
        self.networks_table.setRowCount(0)
        self.networks_table.clear()
        self.networks_table.setHorizontalHeaderLabels(["Network name", "Subnet", "Driver"])
        for network_config in self._networks_list:

            network_name = QTableWidgetItem(network_config["name"])
            network_name.setFlags(Qt.ItemIsEnabled)
            network_subnet = QTableWidgetItem("/".join([network_config["ip_v4"], network_config["subnet"]]))
            network_subnet.setFlags(Qt.ItemIsEnabled)
            network_driver = QTableWidgetItem(network_config["driver"])
            network_driver.setFlags(Qt.ItemIsEnabled)

            self.networks_table.insertRow(self.item_count)
            self.networks_table.setItem(self.item_count, 0, network_name)
            self.networks_table.setItem(self.item_count, 1, network_subnet)
            self.networks_table.setItem(self.item_count, 2, network_driver)
            self.item_count += 1

    def set_configuration(self, networks_list):
        """

        :param networks_list: List of configured networks
        :type networks_list: list
        :return:
        """
        # self._networks_list.append(networks_list)
        networks = []
        for network in networks_list:
            ip_v4, subnet = network["subnet"].split("/")
            networks.append({
            "name": network["name"],
            "ip_v4": ip_v4,
            "subnet": subnet,
            "driver": network["driver"]
            })
        self._networks_list = networks
        self.generate_networks_list()


    def get_current_configuration(self):
        inter = []
        for network in self._networks_list:
            inter.append(
                {
                    "name": network["name"],
                    "subnet": "/".join([network["ip_v4"], network["subnet"]]),
                    "driver": network["driver"]
                }
            )
        self._configuration["networks"] = inter
        return self._configuration

    def get_configured_networks(self):
        return self._networks_list