import os
import time
from colorama import Fore, Style
from .logic_actions_utils import install, upload_file, delete_file, restart_service, add_nameserver

def install_configure_squid(client, instance, arg, verbose=True):
    resolv_conf = open("simulation/workstations/"+instance.name+"/resolv_conf.sh", "w")
    resolv_conf.write("sed -i -e '2 a "+instance.execute(["hostname","-I"]).stdout.split(" ")[1]+" "+instance.name+"' /etc/hosts\n")
    resolv_conf.close()

    upload_file(client, instance, {"instance_path":"/root/resolv_conf.sh", "host_manager_path": "simulation/workstations/"+instance.name+"/resolv_conf.sh"}, verbose=False)
    instance.execute(["chmod","+x","/root/resolv_conf.sh"])
    instance.execute(["./resolv_conf.sh"])
    delete_file(client,instance,{"instance_path":"/root/resolv_conf.sh"}, verbose=False)

    install(client, instance,{"module":"squid3"}, verbose=False)
    instance.execute(["cp","/etc/squid/squid.conf","/etc/squid/squid.conf.origin"])
    delete_file(client,instance,{"instance_path":"/etc/squid/squid.conf"}, verbose=False)

    squid_conf = open("simulation/workstations/"+instance.name+"/squid_conf","w")
    squid_conf.write("visible_hostname dvwa.silicom.com\n")
    ### AUTH_PARAMs
    # ldap_auth
    if arg["ldap_auth"] == {}:
        pass
    else:
        # auth_param basic program /usr/lib/squid3/basic_ldap_auth -b "dc=internet,dc=local" -H ldap://10.159.8.10 -D cn=admin,dc=internet,dc=local -w "my_password" -f "(&(objectclass=person)(cn=%s))"
        squid_conf.write("auth_param basic program /usr/lib/squid3/basic_ldap_auth -b \""+arg["ldap_auth"]["base"]+"\" -H ldap://"+arg["ldap_auth"]["ip"]+" -f \"(uid=%s)\" \n")
    # nsca_auth
    if arg["ncsa_auth"] != []:
        instance.execute(["touch", "/etc/squid/users"])
        for user in arg["ncsa_auth"]:
            instance.execute(["htpasswd", "-b","/etc/squid/users", user[0], user[1]])
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

    upload_file(client, instance, {"instance_path":"/etc/squid/squid.conf", "host_manager_path":"simulation/workstations/"+instance.name+"/squid_conf"}, verbose=False)
    restart_service(client, instance, {"service":"squid"}, verbose=False)

def configure_iptables_proxy(client, instance, arg, verbose=True):
    if arg["proxy_port"] == "":
        arg["proxy_port"] = "3128"
    instance.execute(["iptables","-t","nat","-A","PREROUTING","-s",arg["ip_source"],"-p","tcp","--dport",arg["dport"],"-j","REDIRECT","--to-port",arg["proxy_port"]])

# {"name":"install_configure_squid", "args": {"ldap_auth":{},"ncsa_auth":[],"safe_networks":["10.122.1.0","10.122.0.0"],"safe_ports":["80","443"],"transparent":"true"} },
# {"name":"configure_iptables_proxy", "args": {"ip_source":"10.122.0.0/24", "dport":"80","proxy_port":""} },

# {"name":"install_configure_squid", "args": {"ldap_auth":{},"ncsa_auth":[],"safe_networks":["10.122.1.0","10.122.0.0"],"safe_ports":["443"],"transparent":"true"} },
# {"name":"configure_iptables_proxy", "args": {"ip_source":"10.122.1.0/24", "dport":"443","proxy_port":""} },
