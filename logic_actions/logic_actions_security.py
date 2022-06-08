""" This file contain all function about security configurations """
from colorama import Fore, Style
from logic_actions.logic_actions_utils import wget, create_execute_command_remote_bash, execute_command, install, update, upload_file, delete_file

# def snort_installation(instance, args, verbose=True):
#     """ Install and configure snort in the remote instance """
#     install(instance, {"module":"oinkmaster"}, verbose=False)
#     install(instance, {"module":"snort-rules-default"}, verbose=False)
#     file_snort_install = open("simulation/workstations/"+instance.name+"/file_snort_install.sh", "w")
#     file_snort_install.write("#!/bin/bash\n")
#     file_snort_install.write("########### snort installation ##########\n")
#     file_snort_install.write("echo \"url = http://rules.emergingthreats.net/open-nogpl/snort-2.8.4/emerging.rules.tar.gz\" >> /etc/oinkmaster.conf\n")
#     file_snort_install.write("DEBIAN_FRONTEND=noninteractive apt-get install -y -q snort\n")
#     file_snort_install.write("oinkmaster -o /etc/snort/rules\n")
#     file_snort_install.write("########### snort.conf ##########\n")
#     file_snort_install.write("sed -i -e  \"s|ipvar HOME_NET any|ipvar HOME_NET "+args["network"]+"|\" /etc/snort/snort.conf \n")
#     file_snort_install.close()
#     upload_file(instance, {"instance_path":"/root/file_snort_install.sh", "host_manager_path":"simulation/workstations/"+instance.name+"/file_snort_install.sh"}, verbose=False)
#     execute_command(instance, {"command":["chmod", "+x", "/root/file_snort_install.sh"], "expected_exit_code":"0"}, verbose=False)
#     # instance.execute(["chmod", "+x", "/root/file_snort_install.sh"])
    
#     execute_command(instance, {"command":"./file_snort_install.sh", "expected_exit_code":"0"}, verbose=False)
#     # instance.execute(["./file_snort_install.sh"])
#     delete_file(instance, {"instance_path":"/root/file_snort_install.sh"}, verbose=False)

#     tmp = open("simulation/workstations/"+instance.name+"/local.rules", "w")
#     tmp.write("alert tcp $HOME_NET any -> $EXTERNAL_NET any (msg:\"TEST\"; sid:10000001; rev:1;)")
#     tmp.close()
#     upload_file(instance, {"instance_path":"/etc/snort/rules/local.rules", "host_manager_path":"simulation/workstations/"+instance.name+"/local.rules"}, verbose=False)

#     result = execute_command(instance, {"command":["snort", "-D", "-i", "eth1", "-K", "ascii", "-l", "/var/log/snort/", "-c", "/etc/snort/snort.conf"], "expected_exit_code":"0"}, verbose=False)
#     # result = instance.execute(["snort", "-D", "-i", "eth1", "-K", "ascii", "-l", "/var/log/snort/", "-c", "/etc/snort/snort.conf"])
#     if "exiting (0)" in result.stdout:
#         if verbose:
#             print(Fore.GREEN + "      Snort deamon started !" + Style.RESET_ALL)
#         return 0
#     print(Fore.RED + "      Snort deamon failed ..." + Style.RESET_ALL)
#     return 1

def suricata_installation(instance, verbose=True):
    """ Install ans configure suricata in the remote instance  
        verbose (bool, optional): This argument define if the function prompt some informations during his execution. Default to True.
    Returns:
        int: Return 1 if the function works successfully, otherwise 0.
    """
    install(instance, {"module":"software-properties-common"}, verbose=False)
    execute_command(instance, {"command":["add-apt-repository", "-y", "ppa:oisf/suricata-stable"], "expected_exit_code":"0"}, verbose=False)
    if update(instance, verbose=False) == 1:
        return 1
    
    instance.execute(["apt-cache", "policy", "suricata"])
    if install(instance, {"module":"suricata"}, verbose=False) == 1:
        return 1
    if install(instance, {"module":"suricata-dbg"}, verbose=False) == 1:
        return 1
    
    create_execute_command_remote_bash(instance, {"script_name":"file_suricata_install.sh", "commands":[
                                                                                                 "sed -i -e s#/var/lib/suricata/rules#/etc/suricata/rules# /etc/suricata/suricata.yaml"
                                                                                                ], "delete":"false"}, verbose=False)
   
    execute_command(instance, {"command":["systemctl", "stop", "suricata"], "expected_exit_code":"0"}, verbose=False)
    if verbose:
        print(Fore.GREEN + "      suricata have been installed sucessfully!" + Style.RESET_ALL)
    
    
    execute_command(instance, {"command":["iptables","-I","FORWARD","-j","NFQUEUE"], "expected_exit_code":"0"}, verbose=False)
    execute_command(instance, {"command":["suricata" , "-D", "-c", "/etc/suricata/suricata.yaml","-q","0"], "expected_exit_code":"0"}, verbose=False)

    # Rules
    # wget(instance, {"url":"https://rules.emergingthreats.net/open/suricata/rules/emerging-shellcode.rules", "local_path":"/etc/suricata/rules"}, verbose=False)
   
    return 0

def fail2ban_installation_configuration(instance, arg, verbose=True):
    """ Install and configure fail2ban on remote instance

    Args:
        arg (dict):
            {
                services (list of dict):
                    name (str): This value is the service name inspected by fail2ban.
                    bantime (str): This value represents the time which the user will not be able to connect to the service. 
                    findtime (str): This value is represents which informations will be processed.
                    maxretry (str): This value is the attempts before blocking.
            }
         verbose (bool, optional): This argument define if the function prompt some informations during his execution. Default to True.

    Returns:
        int: Return 1 if the function works successfully, otherwise 0.
    """
    install(instance, {"module":"fail2ban"}, verbose=False)
    custom_jail_conf = open("simulation/workstations/"+instance.name+"/defaults-debian.conf", "w")
    for service in arg["services"]:
        if service["name"] == "samba":
            samba_filter_conf = open("simulation/workstations/"+instance.name+"/filter_samba.conf", "w")
            samba_filter_conf.write("[Definition]\n")
            samba_filter_conf.write("failregex = NT_STATUS_WRONG_PASSWORD.*remoteAddress.*': 'ipv4:<HOST>: \n")
            samba_filter_conf.close()
            if upload_file(instance, {"instance_path":"/etc/fail2ban/filter.d/samba.conf", "host_manager_path":"simulation/workstations/"+instance.name+"/filter_samba.conf"}, verbose=False) == 1:
                return 1

            custom_jail_conf.write("[samba] \n")
            custom_jail_conf.write("enabled = true \n")
            custom_jail_conf.write("port = 139,445 \n")
            custom_jail_conf.write("logpath = /var/log/samba/samba.log \n")
            if service["bantime"] != "":
                custom_jail_conf.write("bandtime = "+service["bantime"]+" \n")
            if service["findtime"] != "":
                custom_jail_conf.write("findtime = "+service["findtime"]+" \n")
            if service["maxretry"] != "":
                custom_jail_conf.write("maxretry = "+service["maxretry"]+" \n")

    custom_jail_conf.close()
    if upload_file(instance, {"instance_path":"/etc/fail2ban/jail.d/defaults-debian.conf", "host_manager_path":"simulation/workstations/"+instance.name+"/defaults-debian.conf"}, verbose=False) == 1:
        return 1
    return 0
