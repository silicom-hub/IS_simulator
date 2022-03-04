import json
from datetime import datetime


class GeneratorJSON:

    def __init__(self, path, network_configuration, physic_configuration, logic_configuration, simulation_configuration):
        current_time = str(datetime.now()).replace(":", "").replace(" ", "_").replace("-", "").split(".")[0]
        self.physic_path = "/".join([path, "{}_physic.json".format(current_time)])
        self.logic_path = "/".join([path, "{}_logic.json".format(current_time)])
        self.simu_path = "/".join([path, "{}_simulation.json".format(current_time)])

        workstation_config = {"workstations": physic_configuration}
        self.physic_config = {}
        self.physic_config.update(network_configuration)
        self.physic_config.update(workstation_config)

        self.logic_config = logic_configuration

        self.simulation_config = simulation_configuration

        self.generate_physic()
        self.generate_logic()
        self.generate_simu()

    def generate_physic(self):
        with open(self.physic_path, 'w') as outfile:
            json.dump(self.physic_config, outfile, indent=4)

    def generate_logic(self):
        logic = []
        # logic_config must be reformatted
        for config in self.logic_config:
            for workstation, actions in config.items():
                logic.append(
                    {
                        "hostname": workstation,
                        "actions": actions
                    }
                )
        with open(self.logic_path, 'w') as outfile:
            json.dump({"workstations": logic}, outfile, indent=4)

    def generate_simu(self):
        config = [sim_config for sim_config in self.simulation_config if sim_config != {}]
        with open(self.simu_path, 'w') as outfile:
            json.dump({"workstations": config}, outfile, indent=4)

    def get_files_path(self):
        return (self.physic_path, self.logic_path, self.simu_path)


class LoaderJSON:

    @staticmethod
    def load_physic_configuration(physic_config):
        networks_list = []
        workstations_list = []
        try:
            with open(physic_config, "r") as physic:
                json_content = json.load(physic)
        except:
            json_content = None

        if json_content is not None:
            networks_list = json_content["networks"]
            workstations_list = json_content["workstations"]

        return networks_list, workstations_list

    @staticmethod
    def load_logic_configuration(logic_config):
        workstations_list = []
        try:
            with open(logic_config, "r") as logic:
                json_content = json.load(logic)
        except:
            json_content = None

        if json_content is not None:
            workstations_list = json_content["workstations"]

        return workstations_list

    @staticmethod
    def load_simulation_configuration(simu_config):
        workstations_simu = []
        try:
            with open(simu_config, "r") as simu:
                json_content = json.load(simu)
        except:
            json_content = None

        if json_content is not None:
            workstations_simu = json_content["workstations"]

        return workstations_simu
