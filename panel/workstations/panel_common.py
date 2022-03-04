from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from panel.workstations.dependencies.common import WorkstationActions, WorkstationConfiguration
from panel.workstations.panel_simul import WorkstationSimulation

class CommonWorkstation(QWidget):
    def __init__(self, workstation_name, workstation_type):
        super(CommonWorkstation, self).__init__()

        self.workstation_name = workstation_name
        self.workstation_type = workstation_type

        # Widgets
        # Physic configuration
        self.workstation = WorkstationConfiguration(self.workstation_name, self.workstation_type)
        # Actions configuration
        self.actions = WorkstationActions(self.workstation_name, self.workstation_type)
        # Simulation configuration
        self.simulation = WorkstationSimulation(self.workstation_name)
        self.simulation.hide()

        self.set_layout()
        self.basic_actions()

    def set_layout(self):
        """ Set layout

        :return: None
        """
        # Vertical layout
        vertical = QVBoxLayout(self)
        self.activated = QCheckBox("Workstation enabled")
        self.activated.setChecked(True)
        vertical.addWidget(self.activated)
        vertical.addWidget(self.workstation)
        vertical.addWidget(self.actions)
        self.configure_simul = QPushButton("Configure simulation")
        vertical.addWidget(self.configure_simul)

    def basic_actions(self):
        """ Connects signals to slot functions

        :return: None
        """
        self.activated.clicked.connect(self.set_workstation_status)
        self.configure_simul.clicked.connect(self.configure_simulation)

    @pyqtSlot()
    def set_workstation_status(self):
        """

        :return:
        """
        if self.activated.isChecked():
            self.workstation.setEnabled(True)
            self.actions.setEnabled(True)
        else:
            self.workstation.setEnabled(False)
            self.actions.setEnabled(False)

    def update_networks_list(self, networks_list):
        """ Update available networks list """
        self.workstation.update_networks_list(networks_list)

    def set_configuration(self, config):
        """ Set loaded data into corresponding widgets

        :param config: Complete workstation configuration
        :type config: dict
        :return:
        """
        self.workstation.set_configuration(config)
        self.actions.set_configuration(config["actions"])  # TODO : fix issue regarding list parameters
        if "users" in config.keys():
            self.simulation.set_configuration(config["users"])

    def get_configuration(self):
        """ Returns currently set configuration

        :return:
        """
        config = {
            "physic": self.workstation.get_current_configuration(),
            "logic": self.actions.get_current_actions()
        }
        return config

    def configure_simulation(self):
        """ Shows simulation configuration widget """
        users = self.actions.get_available_users()
        self.simulation.set_users(users)
        self.simulation.show()

    def get_simulation_configuration(self):
        """ Get data configured in simulation configuration widget

        :return: Data set in simulation panel
        :rtype: dict
        """
        return self.simulation.get_configuration()

    def check_values(self):
        """ Check values in physic configuration """
        return self.workstation.check_values()
