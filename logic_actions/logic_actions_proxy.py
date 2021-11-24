""" This file contain functions about proxy configuration """
from colorama import Fore, Style
from .logic_actions_utils import execute_command, install, upload_file, delete_file, restart_service

def install_configure_squid(instance, arg, verbose=True):
    """ Install and configure squid on the remote instance"""
    resolv_conf = open("simulation/workstations/"+instance.name+"/resolv_conf.sh", "w")
    resolv_conf.write("sed -i -e '2 a "+instance.execute(["hostname", "-I"]).stdout.split(" ")[1]+" "+instance.name+"' /etc/hosts\n")
    resolv_conf.close()

    if upload_file(instance, {"instance_path":"/root/resolv_conf.sh", "host_manager_path": "simulation/workstations/"+instance.name+"/resolv_conf.sh"}, verbose=False) == 1:
        return 1
    execute_command(instance, {"command":["chmod", "+x", "/root/resolv_conf.sh"], "expected_exit_code":"0"}, verbose=False)
    # instance.execute(["chmod", "+x", "/root/resolv_conf.sh"])
    execute_command(instance, {"command":["./resolv_conf.sh"], "expected_exit_code":"0"}, verbose=False)
    # instance.execute(["./resolv_conf.sh"])
    if delete_file(instance, {"instance_path":"/root/resolv_conf.sh"}, verbose=False) == 1:
        return 1
    if install(instance, {"module":"squid3"}, verbose=False) == 1:
        return 1
    
    execute_command(instance, {"command":["cp", "/etc/squid/squid.conf", "/etc/squid/squid.conf.origin"], "expected_exit_code":"0"}, verbose=False)
    # instance.execute(["cp", "/etc/squid/squid.conf", "/etc/squid/squid.conf.origin"])
    if delete_file(instance, {"instance_path":"/etc/squid/squid.conf"}, verbose=False) == 1:
        return 1

    squid_conf = open("simulation/workstations/"+instance.name+"/squid_conf", "w")
    squid_conf.write("visible_hostname dvwa.silicom.com\n")
    ### AUTH_PARAMs
    # ldap_auth
    if arg["ldap_auth"] == {}:
        pass
    else:
        squid_conf.write("auth_param basic program /usr/lib/squid3/basic_ldap_auth -b \""+arg["ldap_auth"]["base"]+"\" -H ldap://"+arg["ldap_auth"]["ip"]+" -f \"(uid=%s)\" \n")
    # nsca_auth
    if arg["ncsa_auth"] != []:
        instance.execute(["touch", "/etc/squid/users"])
        for user in arg["ncsa_auth"]:
            execute_command(instance, {"command":["htpasswd", "-b", "/etc/squid/users", user[0], user[1]]}, verbose=False)
            # instance.execute(["htpasswd", "-b", "/etc/squid/users", user[0], user[1]])
        squid_conf.write("auth_param basic program /usr/lib/squid3/basic_ncsa_auth /etc/squid/users\n")

    if arg["ldap_auth"] != {} or arg["ncsa_auth"] != []:
        squid_conf.write("auth_param basic children 5\n")
        squid_conf.write("auth_param basic credentialsttl 2 hours\n")

    ### ACLs
    # Safe ports
    for port in arg["safe_ports"]:
        squid_conf.write("acl Safe_ports port "+port+"\n")
    # Safe networks
    for network in arg["safe_networks"]:
        squid_conf.write("acl Safe_networks src "+network+"\n")
    # Proxy auth
    if arg["ncsa_auth"] != []:
        squid_conf.write("acl Users_ncsa proxy_auth REQUIRED\n")
    if arg["ldap_auth"] != {}:
        squid_conf.write("acl Users_ldap proxy_auth REQUIRED\n")

    squid_conf.write("acl CONNECT method CONNECT\n")

    ### http_access
    if arg["ncsa_auth"] != []:
        squid_conf.write("http_access allow Users_ncsa\n")
    if arg["ldap_auth"] != {}:
        squid_conf.write("http_access allow Users_ldap\n")
    squid_conf.write("http_access allow Safe_ports\n")
    squid_conf.write("http_access deny !Safe_ports\n")
    squid_conf.write("http_access allow Safe_networks\n")
    squid_conf.write("http_access deny !Safe_networks\n")

    squid_conf.write("http_access deny all\n")

    ### http_port
    if arg["transparent"] == "true":
        squid_conf.write("http_port 3129\n")
        squid_conf.write("http_port 3128 transparent\n")
    else:
        squid_conf.write("http_port 3128\n")

    squid_conf.write("coredump_dir /var/spool/squid\n")
    squid_conf.write("refresh_pattern ^ftp:           1440    20%     10080\n")
    squid_conf.write("refresh_pattern ^gopher:        1440    0%      1440\n")
    squid_conf.write("refresh_pattern -i (/cgi-bin/|\?) 0     0%      0\n")
    squid_conf.write("refresh_pattern (Release|Packages(.gz)*)$      0       20%     2880\n")
    squid_conf.write("refresh_pattern .               0       20%     4320\n")
    squid_conf.close()

    if upload_file(instance, {"instance_path":"/etc/squid/squid.conf", "host_manager_path":"simulation/workstations/"+instance.name+"/squid_conf"}, verbose=False) == 1:
        return 1
    if restart_service(instance, {"service":"squid"}, verbose=False) == 1:
        return 1
    if verbose:
        print(Fore.GREEN+"      Install and configure squid successfully!"+Style.RESET_ALL)
    return 0

def configure_iptables_proxy(instance, arg, verbose=True):
    """ Configure iptables  """
    if arg["proxy_port"] == "":
        arg["proxy_port"] = "3128"
        execute_command(instance, {"command":["iptables", "-t", "nat", "-A", "PREROUTING", "-s", arg["ip_source"], "-p", "tcp", "--dport", arg["dport"], "-j", "REDIRECT", "--to-port", arg["proxy_port"]], "expected_exit_code":"0"}, verbose=False)
    # instance.execute(["iptables", "-t", "nat", "-A", "PREROUTING", "-s", arg["ip_source"], "-p", "tcp", "--dport", arg["dport"], "-j", "REDIRECT", "--to-port", arg["proxy_port"]])
    if verbose:
        print("")

# {"name":"install_configure_squid", "args": {"ldap_auth":{},"ncsa_auth":[],"safe_networks":["10.122.1.0","10.122.0.0"],"safe_ports":["80","443"],"transparent":"true"} },
# {"name":"configure_iptables_proxy", "args": {"ip_source":"10.122.0.0/24", "dport":"80","proxy_port":""} },

# {"name":"install_configure_squid", "args": {"ldap_auth":{},"ncsa_auth":[],"safe_networks":["10.122.1.0","10.122.0.0"],"safe_ports":["443"],"transparent":"true"} },
# {"name":"configure_iptables_proxy", "args": {"ip_source":"10.122.1.0/24", "dport":"443","proxy_port":""} },
