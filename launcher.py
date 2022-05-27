""" Main script """
import os
import time
import shutil
import random
import argparse
import threading
from pylxd import Client
from colorama import Style, Fore
import netifaces as ni
from visualize                              import generate_topology
from logic_actions.logic_actions_utils      import load_json_file, update, execute_command, install, add_nameserver, clear_nameserver, push_sim_user, configure_iptables_logs, create_local_user, install_python_packages, upload_file, download_file, restart_service, generate_root_ca, generate_middle_certificates, generate_certificates, add_user2group, change_fileorfolder_user_owner, change_fileorfolder_group_owner, create_local_group, git_clone, install_virtual_camera
from logic_actions.logic_actions_web        import install_web_server, install_dvwa, enable_ssl, install_chat_application, install_gnu_social_network, install_pip_server, upload_pip_lib, install_food_delivery_application
from logic_actions.logic_actions_ldap       import ldap_create_domaine, ldap_add_user, ldap_client_config
from logic_actions.logic_actions_dns        import dns_installation, dns_resolve_name
from logic_actions.logic_actions_elk        import install_elk
from logic_actions.logic_actions_mail       import enable_ssl_imapd, enable_ssl_postfix, original_mail_installation
from logic_actions.logic_actions_rsyslog    import rsyslog_client
from logic_actions.logic_actions_proxy      import install_configure_squid, configure_iptables_proxy
from logic_actions.logic_actions_samba      import install_samba, add_share_file
from logic_actions.logic_actions_security   import suricata_installation, fail2ban_installation_configuration
from logic_actions.logic_actions_camera     import install_motion, install_zoneminder
from logic_actions.logic_actions_ssh        import install_openssh_server

#################################
############# Utils #############
#################################
def get_ip_if_default(ip_v4):
    """ Find ip range and gateway of lxdbr0
        Return ip range with random value if arg value is 'default_ip_on_lxdbr0'
        Return lxdbr0 gateway if arg value is 'default_gateway_on_lxdbr0' """
    if ip_v4 == "default_ip_on_lxdbr0":
        return ni.ifaddresses("lxdbr0")[ni.AF_INET][0]["addr"][:-1]+str(random.randint(2, 250))
    if ip_v4 == "default_gateway_on_lxdbr0":
        return ni.ifaddresses("lxdbr0")[ni.AF_INET][0]["addr"]
    return ip_v4

def logic_action(action_name, instance, action_arg=None):
    """ Execute function specify in value 'action_name' """
    if action_name == "update":
        return update(instance, action_arg)
    if action_name == "execute_command":
        return execute_command(instance, action_arg)
    if action_name == "install":
        return install(instance, action_arg)
    if action_name == "add_nameserver":
        return add_nameserver(instance, action_arg)
    if action_name == "install_web_server":
        return install_web_server(instance, action_arg)
    if action_name == "ldap_create_domaine":
        return ldap_create_domaine(instance, action_arg)
    if action_name == "ldap_add_user":
        return ldap_add_user(instance, action_arg)
    if action_name == "ldap_client_config":
        return ldap_client_config(instance, action_arg)
    if action_name == "dns_installation":
        return dns_installation(instance, action_arg)
    if action_name == "dns_resolve_name":
        return dns_resolve_name(instance, action_arg)
    if action_name == "clear_nameserver":
        return clear_nameserver(instance, action_arg)
    if action_name == "install_elk":
        return install_elk(instance, action_arg)
    if action_name == "rsyslog_client":
        return rsyslog_client(instance, action_arg)
    if action_name == "install_dvwa":
        return install_dvwa(instance, action_arg)
    if action_name == "push_sim_user":
        return push_sim_user(instance, action_arg)
    if action_name == "configure_iptables_logs":
        return configure_iptables_logs(instance, action_arg)
    if action_name == "create_local_user":
        return create_local_user(instance, action_arg)
    if action_name == "install_python_packages":
        return install_python_packages(instance, action_arg)
    if action_name == "upload_file":
        return upload_file(instance, action_arg)
    if action_name == "download_file":
        return download_file(instance, action_arg)
    if action_name == "install_configure_squid":
        return install_configure_squid(instance, action_arg)
    if action_name == "configure_iptables_proxy":
        return configure_iptables_proxy(instance, action_arg)
    if action_name == "restart_service":
        return restart_service(instance, action_arg)
    if action_name == "generate_root_ca":
        return generate_root_ca(instance, action_arg)
    if action_name == "generate_middle_certificates":
        return generate_middle_certificates(instance, action_arg)
    if action_name == "generate_certificates":
        return generate_certificates(instance, action_arg)
    if action_name == "enable_ssl":
        return enable_ssl(instance, action_arg)
    if action_name == "enable_ssl_imapd":
        return enable_ssl_imapd(instance, action_arg)
    if action_name == "add_user2group":
        return add_user2group(instance, action_arg)
    if action_name == "change_fileorfolder_user_owner":
        return change_fileorfolder_user_owner(instance, action_arg)
    if action_name == "change_fileorfolder_group_owner":
        return change_fileorfolder_group_owner(instance, action_arg)
    if action_name == "enable_ssl_postfix":
        return enable_ssl_postfix(instance, action_arg)
    if action_name == "create_local_group":
        return create_local_group(instance, action_arg)
    if action_name == "install_samba":
        return install_samba(instance, action_arg)
    if action_name == "add_share_file":
        return add_share_file(instance, action_arg)
    if action_name == "suricata_installation":
        return suricata_installation(instance, action_arg)
    if action_name == "install_chat_application":
        return install_chat_application(instance, action_arg)
    if action_name == "install_gnu_social_network":
        return install_gnu_social_network(instance, action_arg)
    if action_name == "git_clone":
        return git_clone(instance, action_arg)
    if action_name == "install_virtual_camera":
        return install_virtual_camera(instance, action_arg)
    if action_name == "install_motion":
        return install_motion(instance, action_arg)
    if action_name == "install_zoneminder":
        return install_zoneminder(instance, action_arg)
    if action_name == "fail2ban_installation_configuration":
        return fail2ban_installation_configuration(instance, action_arg)
    if action_name == "original_mail_installation":
        return original_mail_installation(instance, action_arg) 
    if action_name == "install_pip_server":
        return install_pip_server(instance, action_arg)
    if action_name == "upload_pip_lib":
        return upload_pip_lib(instance, action_arg)
    if action_name == "install_food_delivery_application":
        return install_food_delivery_application(instance, action_arg)
    if action_name == "install_openssh_server":
        return install_openssh_server(instance, action_arg)

    print(Fore.YELLOW+action_name+" is not in the logic action list!"+Style.RESET_ALL)
    return 1

###########################################################
############# Initialisation de la simulation #############
###########################################################
def init_simulation(physic_config):
    """ Reset temporary workstation's file """
    ##### Delete old workstations path
    workstations = os.listdir("simulation/workstations/")
    for workstation in workstations:
        shutil.rmtree("simulation/workstations/"+workstation)

    ##### Load json file
    conf_physic = load_json_file(physic_config)
    for workstation in conf_physic["workstations"]:
        os.makedirs("simulation/workstations/"+workstation["hostname"])

#######################################################
############# Delete (instances/networks) #############
#######################################################
def delete_simulation(client):
    """ Delete all instances and virtual wetworks """
    delete_instances(client)
    delete_networks(client)
    os.system("sudo modprobe -r v4l2loopback")

## Erase new instances
def delete_instances(client):
    """ Delete all instances"""
    for instance in client.instances.all():
        # if instance.name in instances_name_list:
        try:
            instance.stop(wait=True)
        except:
            pass
        instance.delete(wait=True)
        print(instance.name, " instance was deleted!")

## Erase new networks
def delete_networks(client):
    """elete all networks except enp0s3 and lxdbr0 """
    for network in client.networks.all():
        if network.name not in ["enp0s3", "br-int", "lxdbr0"]:
            try:
                network.delete(wait=True)
                print(network.name, " network was deleted!")
            except:
                pass

#############################################
############# Deploy simulation #############
#############################################
def deploy_physic_simulation(client, machines_with_x11, physic_configuration):
    """ Deploy physic part of the simulation
        It started by virtual networks deployement
        then deploy instances with their features """
    print("#############################################")
    print("###### Deploy networks and workstation ######")
    print("#############################################")
    time_begin_physic_deploy = time.time()
    ##### Load json file
    conf_physic = load_json_file(physic_configuration)

    ##### Create networks
    for network in conf_physic["networks"]:
            print(Style.BRIGHT+"\n ===> Deploy ", network["name"], " network in progress..."+Style.RESET_ALL)
            client.networks.create(name=network["name"], type='bridge',
                                   config={"ipv4.address":network["subnet"], "ipv4.dhcp":"true", "ipv6.dhcp":"false"})
            print(Fore.GREEN+"      Network ", network["name"], " was deployed!"+Style.RESET_ALL)
    
    for network in conf_physic["networks"]:
        os.system("sudo ip a del "+network["subnet"]+" dev "+network["name"])
    time.sleep(10)

    ##### Create virtual devices
    os.system("sudo modprobe -r v4l2loopback")
    command = "sudo modprobe v4l2loopback video_nr="
    camera_inc = 0
    for workstation in conf_physic["workstations"]:
        if workstation["camera"] == "true":
            command = command + str(camera_inc) + ","
            camera_inc = camera_inc +1
    os.system(command[:-1])

    ##### Create workstations
    camera_inc = 0
    for workstation in conf_physic["workstations"]:
        print(Style.BRIGHT+"\n ===> Deploy ", workstation["hostname"], " workstation in progress..."+Style.RESET_ALL)
        devices = {}
        ## Add nic configuration
        for nic in workstation["networks"]:
            nic["ip_v4"] = get_ip_if_default(nic["ip_v4"]) # If ip_v4 is an instruction, find automatically his value
            devices.update({nic["interface"]:{"parent":nic["name"], "nictype":"bridged", "type":"nic", "ipv4.address":nic["ip_v4"], "name":nic["interface"]}})
            print(Fore.GREEN+"      Add ip", nic["ip_v4"], "to interface", nic["interface"], "connected to network", nic["name"]+Style.RESET_ALL)

        ## Create disk
        devices.update({'root': {'path': '/', 'pool':'default', 'type': 'disk'}})

        ## Create x11 profile
        x11_profile = ["default", "x11"]

        ## Add camera
        if "camera" in workstation.keys():
            if workstation["camera"] == "true":
                devices.update({'video0': {'type': 'unix-char', 'path':'/dev/video'+str(camera_inc)}})
                camera_inc = camera_inc+1
                print(Fore.GREEN+"      Add camera device to "+workstation["hostname"]+Style.RESET_ALL)
        
        ## Create instance config
        config = {"name":workstation["hostname"], "source":{"type":"image", "mode":"pull",
                                                            "server":"https://images.linuxcontainers.org",
                                                            "protocol":"simplestreams",
                                                            'alias':workstation["distribution"]+"/"+workstation["release"]+'/amd64'}}
        print(Fore.GREEN + "      OS => " + workstation["distribution"] + ":" + workstation[
            "release"] + Style.RESET_ALL)

        # Add x11 profile to be able to have graphical client
        if workstation["hostname"] in machines_with_x11:
            config["profiles"] = x11_profile
            print(Fore.GREEN+"      Profile x11 added to "+workstation["hostname"]+Style.RESET_ALL)

        instance = client.instances.create(config=config, wait=True)
        instance.devices = devices
        if workstation["hostname"] not in machines_with_x11:
            instance.profiles.clear()
        instance.save(wait=True)
        instance.start(wait=True)

        ## Configure ip
        for nic in workstation["networks"]:
            instance.execute(['ip', 'a', 'add', nic["ip_v4"]+"/"+nic["subnet"], 'dev', nic["interface"]])

        ## Add gateway
        if workstation["gateway"] != "":
            workstation["gateway"] = get_ip_if_default(workstation["gateway"]) # If gateway is an instruction, find automatically his value
            instance.execute(['ip', 'route', 'add', 'default', 'via', workstation["gateway"]])
        else:
            print(Fore.YELLOW+"No gateway!"+Style.RESET_ALL)

        ## Create environnement [folder ,variable environnement]
        result = instance.execute(['mkdir', "/root/.env"])
        if result.exit_code == 0:
            print(Fore.GREEN+"      Directory for environnement variables was created! ", str(result.exit_code)+Style.RESET_ALL)
        else:
            print(Fore.RED+"      Error during folder creation for environnement variables: ", str(result.exit_code)+Style.RESET_ALL)


        print(Fore.GREEN+"      Workstation", workstation["hostname"], "has been started!"+Style.RESET_ALL)

    print(Fore.BLUE+" Physic elapsed time: "+str(time.time()-time_begin_physic_deploy)+Style.RESET_ALL)

################################################
############# Configure simulation #############
################################################
def configuration_logic_simulation(client, logic_configuration):
    """ Apply every configurations specify in 'conf_logicjson' for each instances """
    conf_logic = load_json_file(logic_configuration)
# try:
    for workstation in conf_logic["workstations"]:
        instance = client.instances.get(workstation["hostname"])
        print()
        print("########################################")
        print("Begin", instance.name, "configuration...")
        print("########################################")
        for action in workstation["actions"]:
            time_begin_logic = time.time()
            print(Style.BRIGHT+" ===>", action["name"]+Style.RESET_ALL)
            try: # Function have arguments
                logic_action(action["name"], instance, action["args"])
            except: # Function haven't argument
                logic_action(action["name"], instance)
            print(Fore.BLUE+" Elapsed time: "+ str(time.time()-time_begin_logic)+Style.RESET_ALL)
# except:
    # print(Fore.RED+"ERROR during logics_actions process!"+Style.RESET_ALL)
    # input("Waiting...\n")
    # delete_simulation(client)

#########################################
# Launch user sim
#########################################
class Thread_user_sim(threading.Thread):
    def __init__(self, instance):
        threading.Thread.__init__(self)
        self.instance = instance

    def run(self):
        print("Launch user simulation on ", self.instance.name)
        print(self.instance.execute(["python3", "/sim_user/manager.py"]).stdout)
        print()
        print("="*25)


def launch_user_sim(client, logic_configuration):
    """ Launch live script for each users of each workstations """
    print()
    print("########################################")
    print("########## User simulation ... #########")
    print("########################################")
    conf_logic = load_json_file(logic_configuration)
    for workstation in conf_logic["workstations"]:
        for action in workstation["actions"]:
            if action["name"] == "push_sim_user":
                instance = client.instances.get(workstation["hostname"])
                thread = Thread_user_sim(instance)
                thread.start()
                time.sleep(15)


def main(physic_config=None, logic_config=None):
    # Setting default file
    if physic_config is None:
        physic_config = "simulation/Configurations/conf_physic.json"
    if logic_config is None:
        logic_config = "simulation/Configurations/conf_logic.json"

    PROG_DESCRIPTION = """This launcher will start a simulation of a network using lxd containers.
    It might take some time so sit back and relax. 
    At the end the program will wait for a user input before deleting the simulation."""
    ARGS_PARSER = argparse.ArgumentParser(description=PROG_DESCRIPTION)

    ARGS_PARSER.add_argument("-x11", "--enable-x11-on", dest="machines_with_x11", action="store",
                             default=[], help="""
        Enable X11 server (GUI) on all the machines specified.
        To use this argument you must first create the x11 profile (see Readme).
        You can then launch application with a graphical interface an see what's happening from the host.
        To do so, be sure to properly install the application and then add an action to launch it or use the terminal.
    """)
    ARGS_PARSER.add_argument("-g", "--graph-simulation", action="store_true",
                             help="""
        Print simulation graph
    """)

    ARGS = ARGS_PARSER.parse_args()
    TIME_BEGIN_DEPLOYEMENT = time.time()

    CLIENT = Client()
    delete_simulation(CLIENT)
    init_simulation(physic_config)
    if ARGS.graph_simulation:
        generate_topology(filename=physic_config)

    deploy_physic_simulation(CLIENT, ARGS.machines_with_x11, physic_config)
    configuration_logic_simulation(CLIENT, logic_config)
    print(Fore.BLUE+" Elapsed deployement time "+str(time.time()-TIME_BEGIN_DEPLOYEMENT)+Style.RESET_ALL)
    print()
    launch_user_sim(CLIENT, logic_config)

    input("Waiting...\n")
    delete_simulation(CLIENT)


################################
############# MAIN #############
################################
if __name__ == "__main__":
    main()