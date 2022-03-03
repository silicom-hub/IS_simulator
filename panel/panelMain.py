# Qt
from PyQt5.Qt import pyqtSlot

# Basics
from threading import Thread, ThreadError

# Dependencies
from panel.workstations.panel_common import CommonWorkstation
from panel.workstations.panel_router import RouterConfiguration
from panel.workstations.panel_networks import NetworksConfiguration

from panel.common.CommonWidgets import *

# JSON generator
from common.generator_json import GeneratorJSON, LoaderJSON

from common.config import Config, compare_d_lists

# Main part of the software
import launcher


class PanelMain(QWidget):
    def __init__(self):
        super(PanelMain, self).__init__()

        # Load available workstations
        self.workstations_list = self.load_workstations_available()

        self.resize(QSize(1750, 900))
        self.setWindowTitle("SI Simulator V{}".format(Config.get_version()))
        self.set_layout()

        # Init networks config
        self.network_configuration = NetworksConfiguration()
        init_router = RouterConfiguration("router")
        init_dns = CommonWorkstation("dns", "dns")
        self.multi_window.addTab(self.network_configuration, "networks")
        self.multi_window.addTab(init_router, "router")
        self.multi_window.addTab(init_dns, "dns")
        self.active_configurations = [init_router, init_dns]
        self.j_gen = None
        self.main_thread = None

        self.connect_actions()

    def load_workstations_available(self):
        """ Get workstation types available for configure simulation

        :return: Workstation types
        :rtype: list
        """
        return Config.get_available_workstations()

    def set_layout(self):
        """ Set layout """
        # Create main layout
        self.main_layout = QGridLayout(self)
        # Workstation creation area
        self.workstations_available = QComboBox()
        for workstation in self.workstations_list:
            self.workstations_available.addItem(workstation)
        self.workstations_available.setCurrentIndex(self.workstations_available.findText("workstation"))
        self.add_workstation = QPushButton("Add workstation")
        name_label = QLabel("Workstation name : ")
        self.workstation_name_value = QLineEdit()
        workstation_type_label = QLabel("Type:")

        # Workstations configuration area
        self.multi_window = QTabWidget()
        self.multi_window.setTabsClosable(True)

        self.main_layout.addWidget(name_label, 0, 0)
        self.main_layout.addWidget(self.workstation_name_value, 0, 1)
        self.main_layout.addWidget(workstation_type_label, 0, 3)
        self.main_layout.addWidget(self.workstations_available, 0, 4)
        self.main_layout.addWidget(self.add_workstation, 0, 5)
        self.main_layout.addWidget(self.multi_window, 2, 0, 1, 6)

        group_actions = QGroupBox("Simulation")
        group_layout = QGridLayout()

        self.launcher_button = QPushButton("Save configuration")
        group_layout.addWidget(self.launcher_button, 0, 0)
        self.loader_button = QPushButton("Load configuration")
        group_layout.addWidget(self.loader_button, 1, 0)
        self.check_configuration = QPushButton("Verify configuration")
        group_layout.addWidget(self.check_configuration, 2, 0)

        group_actions.setLayout(group_layout)
        self.main_layout.addWidget(group_actions, 3, 0, 1, 8)

    def connect_actions(self):
        """ Connect signals to dedicated functions """
        self.add_workstation.clicked.connect(self.add_selected_workstation)
        self.workstation_name_value.returnPressed.connect(self.add_selected_workstation)
        self.multi_window.currentChanged.connect(self.update_networks_list)
        self.launcher_button.clicked.connect(self.generate_configuration)
        self.loader_button.clicked.connect(self.load_configuration)
        self.check_configuration.clicked.connect(self.check_parameters)
        # Tab signal
        self.multi_window.tabCloseRequested.connect(self.close_tab)

    @pyqtSlot()
    def add_selected_workstation(self):
        workstation = self.workstation_name_value.text()
        if workstation != "":
            type = self.workstations_available.currentText()
            if type != "router":
                workstation_configuration = CommonWorkstation(workstation, type)
            else:
                workstation_configuration = RouterConfiguration(workstation)
            self.active_configurations.append(workstation_configuration)
            self.multi_window.addTab(workstation_configuration, workstation)
        else:
            PopUpWidget("Please enter a workstation name")

    @pyqtSlot()
    def update_networks_list(self):
        # Get networks basic configuration
        networks_list = self.network_configuration.get_configured_networks()
        networks_update = []
        # Update using configuration in router configurations
        for workstation in self.active_configurations:
            if workstation.workstation_type in ["router"]:
                networks_update += workstation.get_networks_list()

        # Compare lists to determine if networks configuration has been updated
        try:
            networks_list = compare_d_lists(networks_list, networks_update)
        except:
            pass

        for workstation in self.active_configurations:
            workstation.update_networks_list(networks_list)

    @pyqtSlot()
    def generate_configuration(self):
        """

        :return:
        """
        # File dialog : select target directory
        try:
            dial = QFileDialog()
            dial.setBaseSize(QSize(1480, 900))
            dial.setAcceptMode(dial.AcceptMode(1))
            directory = dial.getExistingDirectory(options=QFileDialog.DontUseNativeDialog)

            network_configuration = self.network_configuration.get_current_configuration()
            physic_configuration = [workstation.get_configuration()["physic"] for workstation in self.active_configurations]
            logic_configuration = [workstation.get_configuration()["logic"] for workstation in self.active_configurations]
            simulation_configuration = [workstation.get_simulation_configuration() for workstation in self.active_configurations]

            if directory not in [""]:
                # Generating json file
                self.j_gen = GeneratorJSON(
                    directory,
                    network_configuration,
                    physic_configuration,
                    logic_configuration,
                    simulation_configuration
                )
        except:
            pass

    @pyqtSlot()
    def start_simulation(self):
        if self.j_gen is not None:
            phy, logi, simu = self.j_gen.get_files_path()
            self.main_thread = Thread(target=launcher.main, args=(phy, logi,))
            try:
                self.main_thread.start()
            except ThreadError:
                raise

    @pyqtSlot()
    def interrupt_simulation(self):
        if self.main_thread is not None:
            # It is not going to be easy as expected
            # self.main_thread.join()
            pass

    @pyqtSlot()
    def load_configuration(self):
        physic_config = openConfigFile()

        ext = physic_config.split(".")
        if ext[-1] not in ["json"]:
            return
        if physic_config in [""]:
            return

        logic_config = openConfigFile()

        ext = logic_config.split(".")
        if ext[-1] not in ["json"]:
            return
        if logic_config in [""]:
            return

        simulation_config = openConfigFile()
        ext = simulation_config.split(".")
        if ext[-1] not in ["json"]:
            return
        if simulation_config in [""]:
            return

        # Generating json file
        networks, workstations = LoaderJSON.load_physic_configuration(physic_config)
        logic = LoaderJSON.load_logic_configuration(logic_config)
        simu = LoaderJSON.load_simulation_configuration(simulation_config)

        self.multi_window.clear()
        self.network_configuration = NetworksConfiguration()
        self.network_configuration.set_configuration(networks)
        self.multi_window.addTab(self.network_configuration, "networks")
        self.active_configurations = []
        loaded_config = {}
        # Join dictionaries by hostnames
        for workstation in workstations:
            for l_workstation in logic:
                if workstation["hostname"] == l_workstation["hostname"]:
                    workstation.update(l_workstation)  # Add key actions to dictionary
            for simu_workstation in simu:
                if workstation["hostname"] == simu_workstation["hostname"]:
                    workstation.update(simu_workstation)  # Add key actions to dictionary
            loaded_config[workstation["hostname"]] = workstation
        # Creating config pages with loaded data
            if "router" not in workstation["hostname"]:
                config = CommonWorkstation(workstation["hostname"], "workstation")
            else:
                config = RouterConfiguration(workstation["hostname"])
            self.active_configurations.append(config)

        self.update_networks_list()

        for config in self.active_configurations:
            if config.workstation_name in loaded_config.keys():
                config.set_configuration(loaded_config[config.workstation_name])
                self.multi_window.addTab(config, config.workstation_name)

    @pyqtSlot(int)
    def close_tab(self, tab_index):
        if tab_index != -1 and tab_index >= 1:
            # Networks cannot be closed
            self.multi_window.removeTab(tab_index)
            self.active_configurations.pop(tab_index - 1)

    @pyqtSlot()
    def check_parameters(self):
        corrections = ""
        for workstation in self.active_configurations:
            corrections += "In workstation {}\n".format(workstation.workstation_name)
            workstation_status = workstation.check_values()
            for key, status in workstation_status.items():
                if not status:
                    corrections += "Parameter {} must be corrected\n".format(
                        key
                    )
        pop = PopUpWidget(corrections)
        pop.show()
