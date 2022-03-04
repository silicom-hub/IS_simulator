from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from panel.workstations.dependencies.common import WorkstationActions


class RouterConfiguration(QWidget):
    def __init__(self, router_name):
        super(RouterConfiguration, self).__init__()
        self.workstation_name = router_name
        self.workstation_type = "router"
        self.actions = WorkstationActions(self.workstation_name, self.workstation_type)
        self.create_router_widget()
        self.item_count = 0
        self.networks_available = {}

        self.connect_actions()

    def create_router_widget(self):
        vertical = QVBoxLayout(self)
        # Labels
        self.name_label = QLabel("Workstation name")
        self.distribution_label = QLabel("Distribution")
        self.release_label = QLabel("Release")

        # Network labels
        self.network_name_label = QLabel("Network name")

        #
        self.gateway_label = QLabel("Gateway")
        self.camera_label = QCheckBox("Camera")

        # Line Edits
        self.name_value = QLabel(self.workstation_name)
        self.distribution_value = QLineEdit()
        self.distribution_value.setText("ubuntu")
        self.release_value = QLineEdit()
        self.release_value.setText("bionic")
        self.network_name_value = QComboBox()
        self.gateway_value = QLineEdit()
        self.gateway_value.setText("default_gateway_on_lxdbr0")

        # Router table
        self.router_table = QTableWidget()
        self.router_table.setMinimumHeight(250)
        self.router_table.insertColumn(0)
        self.router_table.setColumnWidth(0, 400)
        self.router_table.insertColumn(1)
        self.router_table.setColumnWidth(1, 150)
        self.router_table.insertColumn(2)
        self.router_table.setColumnWidth(2, 300)
        self.router_table.insertColumn(3)
        self.router_table.setColumnWidth(3, 150)
        self.router_table.setHorizontalHeaderLabels(["Name", "Interface", "IP v4", "Subnet"])

        # Add network button
        self.add_network_router = QPushButton("Add network")
        self.remove_network_router = QPushButton("Remove network")

        # Group box
        self.group_box = QGroupBox()
        self.group_box.setTitle('router configuration')
        self.group_box.setMaximumHeight(500)
        # Grid layout
        grid_layout = QGridLayout()
        # Workstation name
        grid_layout.addWidget(self.name_label, 0, 0)
        grid_layout.addWidget(self.name_value, 0, 1)
        # Distribution name
        grid_layout.addWidget(self.distribution_label, 0, 3)
        grid_layout.addWidget(self.distribution_value, 0, 4)
        # Release name
        grid_layout.addWidget(self.release_label, 0, 6)
        grid_layout.addWidget(self.release_value, 0, 7)

        # Network
        grid_layout.addWidget(self.network_name_label, 1, 0)
        grid_layout.addWidget(self.network_name_value, 1, 1, 1, 5)
        grid_layout.addWidget(self.add_network_router, 1, 7)
        grid_layout.addWidget(self.remove_network_router, 1, 8)

        grid_layout.addWidget(self.router_table, 2, 0, 1, 9)

        # Other parameters
        grid_layout.addWidget(self.gateway_label, 3, 0)
        grid_layout.addWidget(self.gateway_value, 3, 1)

        grid_layout.addWidget(self.camera_label, 3, 3)

        self.group_box.setLayout(grid_layout)

        vertical.addWidget(self.group_box)
        vertical.addWidget(self.actions)

    def update_networks_list(self, networks_list):
        # Get current text
        former_network = self.network_name_value.currentText()
        # Clean combo box
        self.network_name_value.clear()
        # Recreate networks list
        for network in networks_list:
            # Update dictionary
            stored_config = {
                str(network["name"]): {
                    "ip_v4": network["ip_v4"],
                    "subnet": network["subnet"],
                    "driver": network["driver"]
                }
            }
            self.networks_available.update(stored_config)
            # Update network list
            self.network_name_value.addItem(network["name"])
        # Check if formerly selected network is available
        former_index = self.network_name_value.findText(former_network)
        self.network_name_value.setCurrentIndex(former_index)

    def connect_actions(self):
        self.add_network_router.clicked.connect(self.add_network)
        self.remove_network_router.clicked.connect(self.remove_network)

    def check_values(self):
        dist = True if self.distribution_value.text() in ["ubuntu", "debian"] else False

        assertion = {
            "distribution": dist,  # if wrong distribution set
        }

        return assertion

    @pyqtSlot()
    def add_network(self):
        network_name = self.network_name_value.currentText()
        ip = self.networks_available[network_name]["ip_v4"]
        subnet = self.networks_available[network_name]["subnet"]
        # to_split = self.networks_available[network_name]["subnet"]
        # ip, subnet = to_split.split("/")
        driver = self.networks_available[network_name]["driver"]
        self.set_network(network_name, ip, subnet)

    def set_network(self, name, ip, subnet, interface=""):
        network_name = QTableWidgetItem(name)
        network_name.setFlags(Qt.ItemIsEnabled)
        network_interface = QTableWidgetItem(interface)
        network_ip = QTableWidgetItem(ip)
        network_ip.setFlags(Qt.ItemIsEnabled)
        network_subnet = QTableWidgetItem(subnet)
        network_subnet.setFlags(Qt.ItemIsEnabled)

        self.router_table.insertRow(self.item_count)
        self.router_table.setItem(self.item_count, 0, network_name)
        self.router_table.setItem(self.item_count, 1, network_interface)
        self.router_table.setItem(self.item_count, 2, network_ip)
        self.router_table.setItem(self.item_count, 3, network_subnet)
        self.item_count += 1

    @pyqtSlot()
    def remove_network(self):
        try:
            index = self.router_table.currentRow()
            self.router_table.removeRow(index)
            self.item_count -= 1
        except:
            pass

    def set_configuration(self, config):
        """

        :param config:
        :type config: dict
        :return:
        """
        self.item_count = 0
        self.name_value.setText(config["hostname"])
        self.distribution_value.setText(config["distribution"])
        self.release_value.setText(config["release"])
        self.gateway_value.setText(config["gateway"])
        self.camera_label.setChecked(config["camera"] in ["true"])

        for network in config["networks"]:
            self.set_network(network["name"], network["ip_v4"], network["subnet"], network["interface"])

        self.actions.set_configuration(config["actions"])

    def get_configuration(self):
        config = {
            "physic": self.get_physic_configuration(),
            "logic": self.actions.get_current_actions(),
        }
        return config

    def get_simulation_configuration(self):
        return {}

    def get_physic_configuration(self):
        _configuration = {
            "hostname": self.name_value.text(),
            "distribution": self.distribution_value.text(),
            "release": self.release_value.text(),
            "networks" : self.get_networks_list(),
            "gateway": self.gateway_value.text(),
            "camera": str(self.camera_label.isChecked()).lower()
        }
        return _configuration

    def get_networks_list(self):
        """ Apply networks defined in networks tab to every other tab

        :return: None
        """
        # Create a list containing dict with required data
        # for item in self.router_table
        networks = []
        for index in range(self.router_table.rowCount()):
            network_name = self.router_table.item(index, 0).text()
            interface = self.router_table.item(index, 1).text()
            ip = self.router_table.item(index, 2).text()
            subnet = self.router_table.item(index, 3).text()
            networks.append(
                {
                    "name": network_name,
                    "interface": interface,
                    "ip_v4": ip,
                    "subnet": subnet
                }
            )

        return networks
