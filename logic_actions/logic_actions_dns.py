""" This file contains all function for DNS configuration """
from colorama import Fore, Style
from .logic_actions_utils import execute_command, install, upload_file, restart_service

################################################

################################################
def inverse_ip(ip_v4):
    """ Inverse ip order a.b.c.d -> d.c.b.a """
    tmp = ip_v4.split(".")
    tmp.reverse()
    return ".".join(tmp)

def add_zone_named_conf(instance, db_filename):
    """ Push name resolution file named.conf.local in /etc/bind/ on the remote instance"""
    resolution_file = open("simulation/workstations/"+instance.name+"/named.conf.local", "a+")
    resolution_file.write("zone \""+ db_filename +"\" {\n")
    resolution_file.write("type master;\n")
    resolution_file.write("file \"/etc/bind/db."+db_filename+"\";\n")
    resolution_file.write("};\n")
    resolution_file.close()
    if upload_file(instance, {"instance_path":"/etc/bind/named.conf.local", "host_manager_path":"simulation/workstations/"+instance.name+"/named.conf.local"}, verbose=False) == 1:
        return 1
    return 0

def dns_installation(instance, arg, verbose=True):
    """ Install bind9 package on the remote instance and configure name resolution for his own domain name """
    if install(instance, {"module":"bind9"}, verbose=False) == 1:
        return 1
    if dns_resolve_name(instance, {"domain_name":arg["domain_name"], "ip_resolution":arg["ip_resolution"], "mail":"", "alias":""}, verbose=False) == 1:
        return 1
    execute_command(instance, {"command":["chmod", "+r", "/etc/bind/named.conf.local"], "expected_exit_code":"0"}, verbose=False)
    if restart_service(instance, {"service":"bind9"}, verbose=False) == 1:
        return 1
    if verbose:
        print(Fore.GREEN+ "      Service bind9 has been installed and configured successfully!"+Style.RESET_ALL)
    return 0

def dns_resolve_name(instance, arg, verbose=True):
    """ Create file for name resolution and ip resolution and push it on the remote instance """
    install(instance, {"module":"dnsutils"}, verbose=False)
    # db config
    resolution_file = open("simulation/workstations/"+instance.name+"/db."+arg["domain_name"], "w")
    resolution_file.write("$TTL       604800\n")
    resolution_file.write("@       IN      SOA     "+ arg["domain_name"] +". root."+ arg["domain_name"] +". (\n")
    resolution_file.write("                                 3       ;     Serial\n")
    resolution_file.write("                            604800       ;     Refresh\n")
    resolution_file.write("                             86400       ;     Retry\n")
    resolution_file.write("                           2419200       ;     Expire\n")
    resolution_file.write("                            604800   )   ;     Negative Cache TTL\n")

    resolution_file.write(";\n")
    resolution_file.write("; name servers - NS records\n")

    resolution_file.write("@        IN      NS      "+ arg["domain_name"]+".\n")
    if arg["alias"] != [""]:
        for alias in arg["alias"]:
            resolution_file.write(alias+"."+arg["domain_name"]+".   IN      CNAME       "+arg["domain_name"]+".\n")

    resolution_file.write(arg["domain_name"] +".   IN      A       "+ arg["ip_resolution"]+"\n")
    if arg["mail"] != "":
        resolution_file.write("@     IN      MX     10     "+arg["domain_name"] +".\n")
    resolution_file.close()
    # named.conf.local
    if add_zone_named_conf(instance, arg["domain_name"]) == 1:
        return 1

    if upload_file(instance, {"instance_path":"/etc/bind/db."+arg["domain_name"], "host_manager_path":"simulation/workstations/"+instance.name+"/db."+arg["domain_name"]}, verbose=False) == 1:
        return 1
    execute_command(instance, {"command":["chmod", "+r", "/etc/bind/db."+arg["domain_name"]], "expected_exit_code":"0"}, verbose=False)
    # instance.execute(["chmod", "+r", "/etc/bind/db."+arg["domain_name"]])

    #db.inverse
    resolution_inverse_file = open("simulation/workstations/"+instance.name+"/db."+inverse_ip(arg["ip_resolution"])+".in-addr.arpa", "w")
    resolution_inverse_file.write("$TTL       604800\n")
    resolution_inverse_file.write("@       IN      SOA     "+ arg["domain_name"] +". root."+ arg["domain_name"] +". (\n")
    resolution_inverse_file.write("                                 3       ;     Serial\n")
    resolution_inverse_file.write("                            604800       ;     Refresh\n")
    resolution_inverse_file.write("                             86400       ;     Retry\n")
    resolution_inverse_file.write("                           2419200       ;     Expire\n")
    resolution_inverse_file.write("                            604800   )   ;     Negative Cache TTL\n")
    resolution_inverse_file.write("@        IN      NS      localhost.\n")
    resolution_inverse_file.write("         IN      PTR     "+arg["domain_name"]+".\n")
    resolution_inverse_file.close()
    if upload_file(instance, {"instance_path":"/etc/bind/db."+inverse_ip(arg["ip_resolution"])+".in-addr.arpa", "host_manager_path":"simulation/workstations/"+instance.name+"/db."+inverse_ip(arg["ip_resolution"])+".in-addr.arpa"}, verbose=False) == 1:
        return 1

    # named.conf.local
    if add_zone_named_conf(instance, inverse_ip(arg["ip_resolution"])+".in-addr.arpa") == 1:
        return 1
    execute_command(instance, {"command":["chmod", "+r", "/etc/bind/db."+inverse_ip(arg["ip_resolution"])+".in-addr.arpa"], "expected_exit_code":"0"}, verbose=False)
    execute_command(instance, {"command":["chmod", "+r", "/etc/bind/named.conf.local"], "expected_exit_code":"0"}, verbose=False)
    if restart_service(instance, {"service":"bind9"}, verbose=False) == 1:
        return 1

    result = execute_command(instance, {"command":["nslookup", arg["domain_name"], "127.0.0.1"], "expected_exit_code":"0"}, verbose=False)
    if "SERVFAIL" in result:
        print(Fore.RED+"      Error during adding new resolution name"+Style.RESET_ALL)
        return 1
    if verbose:
        print(Fore.GREEN+"      New resolution file for "+arg["domain_name"]+" and bind9 service have been restarted!"+Style.RESET_ALL)

    result = execute_command(instance, {"command":["nslookup", arg["ip_resolution"], "127.0.0.1"], "expected_exit_code":"0"}, verbose=False)
    # result = instance.execute(["nslookup", arg["ip_resolution"], "127.0.0.1"])
    if "SERVFAIL" in result:
        print(Fore.RED+"      Error during adding new inverse resolution name"+Style.RESET_ALL)
        return 1
    if verbose:
        print(Fore.GREEN+"      New inverse resolution file for "+arg["ip_resolution"]+" and bind9 service have been restarted!"+Style.RESET_ALL)
    return 0
