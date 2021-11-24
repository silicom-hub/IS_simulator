""" This file implement functions to visualize the simulation with a graph """
import json
from graphviz import Graph

def load_json_file(path_conf):
    """ Loads a json file specified in the path """
    with open(path_conf, "r", encoding="utf-8") as file_conf:
        conf_physic = json.load(file_conf)
    return conf_physic

def get_info_machine(conf_physic, hostname):
    """ Get all workstaions informations """
    for workstation in conf_physic["workstations"]:
        machine_label = "Hostname: "+workstation["hostname"]+"\nDistribution: "+workstation["distribution"]+"\nRelease: "+workstation["release"]+"\nCamera: "+workstation["camera"]
        if workstation["hostname"] == hostname:
            return machine_label
    return 1

def generate_topology(filename="simulation/Configurations/conf_physic.json"):
    """ Generate topology of actual network in conf_physic.json """
    graph = Graph(engine="circo")
    conf_physic = load_json_file(filename)
    graph.node("lxdbr0", color="red", label="lxdbr0")
    for network in conf_physic["networks"]:
        network_lablel = f"{network['name']} \n IP range: {network['subnet']}"
        graph.node(network["name"], color="red", label=network_lablel)

    for workstation in conf_physic["workstations"]:
        workstation_label = get_info_machine(conf_physic, workstation["hostname"])
        graph.node(workstation["hostname"], color="blue", label=workstation_label, shape="box")
        for network in workstation["networks"]:
            graph.edge(workstation["hostname"], network["name"],
                       label="Interface: "+network["interface"]+"\nip_v4: "+network["ip_v4"],
                       constraint='false')
    graph.render("graph.gv", view=True)
