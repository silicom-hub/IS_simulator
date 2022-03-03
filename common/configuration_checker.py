import os
from common.config import Config


class ConfigurationChecker:
    def __init__(self, physic_configuration, logic_configuration):
        self.physic = physic_configuration
        self.logic = logic_configuration

    def check_physic_configuration(self):
        dist = True if self.physic["distribution"] in ["ubuntu", "debian"] else False
        release = True if self.physic["release"] in ["xenial, bionic, focal"] else False
        network = True if self.physic["network_name"] not in [""] else False
        split_ip = self.physic["ip_address"].split(".")
        ip = True if split_ip[-1] not in [""] else False
        gateway = True if split_ip[-1] not in [""] else False

        assertion = {
            "distribution": dist,  # if wrong distribution set
            "release": release, # if wrong release set
            "network": network,  # if wrong network name set
            "ip": ip,  # if ip address is incomplete,
            "gateway": gateway  # if gateway is incomplete
        }

        return assertion

    def check_logic_configuration(self):
        # logic configuration is a list of dictionaries
        iter_result = map(self.logic, self.check_logic_actions)
        return list(iter_result)

    def check_logic_actions(self, arg_dict):
        # Each arg_dict contains a single key, value
        for key, value in arg_dict.items():
            if value in Config.get_authorized_values(key):
                return True
        return False
