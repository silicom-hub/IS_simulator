""" This file contains all function for DNS configuration """
from typing import Optional
from colorama import Fore, Style
from .logic_actions_utils import execute_command, install, upload_file, restart_service

################################################

################################################
def inverse_ip(ip_v4: str) -> str:
    """ Inverse ip order
    
    Args:
        ip_v4 (string): This argument represent an ip address 'a.b.c.d'

    Returns:
        string: This value is an ip address who inversed ip_v4 'd.c.b.a'

    Examples:
        a.b.c.d -> d.c.b.a
    """

    tmp = ip_v4.split(".")
    tmp.reverse()
    return ".".join(tmp)

def add_zone_named_conf(instance: object, domain_name: str) -> int:
    """ Push name resolution file named.conf.local in /etc/bind/ on the remote instance.
    
    Args:
        instance (object): This argmument define the lxc instance
        domain_name (str): This argument is the domain name who will be associated.

    Returns:
        int: Return 1 if the function works successfully, otherwise 0.    
    """

    resolution_file = open("simulation/workstations/"+instance.name+"/named.conf.local", "a+")
    resolution_file.write("zone \""+ domain_name +"\" {\n")
    resolution_file.write("type master;\n")
    resolution_file.write("file \"/etc/bind/db."+domain_name+"\";\n")
    resolution_file.write("};\n")
    resolution_file.close()
    if upload_file(instance, {"instance_path":"/etc/bind/named.conf.local", "host_manager_path":"simulation/workstations/"+instance.name+"/named.conf.local"}, verbose=False) == 1:
        return 1
    return 0

def dns_installation(instance: object, arg: dict, verbose: bool=True) -> int:
    """ Install bind9 package on the remote instance and configure name resolution for his own domain name.

    Args:
        instance (object): This argmument define the lxc instance
        arg (dict of str: Optional): This argument list maps arguments and their value.
            {
                domain_name (str): This argument is the domain name who will be associated with an ip.
                ns (str): This argument specify the domain name of the DNS authority server for this domain.
                ip_resolution (str): This argument is the ip associated to the domain name. 
                forwarder (list of str): This argument is a list of ip address that the dns server can contact 
                                         to find mapping between a domain name and an ip address that it doesn't know.

            }
        verbose (bool, optional): This argument define if the function prompt some informations during his execution. Default to True.

    Returns:
        int: Return 1 if the function works successfully, otherwise 0.
    """

    if install(instance, {"module":"bind9"}, verbose=False) == 1:
        return 1
    # execute_command(instance, {"command":["truncate", "-s", "0", "/etc/bind/db.root"], "expected_exit_code":"0"}, verbose=False)
    if dns_resolve_name(instance, {"domain_name":arg["ns"], "ns":arg["ns"], "ip_resolution":arg["ip_resolution"], "mail":"", "alias":""}, verbose=False) == 1:
        return 1
    execute_command(instance, {"command":["chmod", "+r", "/etc/bind/named.conf.local"], "expected_exit_code":"0"}, verbose=False)
    
    options = open("simulation/workstations/"+instance.name+"/named.conf.options", "w")
    options.write("options { \n")
    options.write("   directory \"/var/cache/bind\"; \n")
    options.write("   dnssec-validation no; \n")
    options.write("   auth-nxdomain no;    # conform to RFC1035 \n")
    options.write("   listen-on-v6 { any; }; \n")
    if arg["forwarders"] != []:
        options.write("   recursion yes; \n")
        options.write("   forward only; \n")
        options.write("   forwarders { ")
        for forwarder in arg["forwarders"]:
            options.write(forwarder+"; ")
        options.write(" }; \n")
    options.write("}; \n")
    options.close()
    if upload_file(instance, {"instance_path":"/etc/bind/named.conf.options", "host_manager_path":"simulation/workstations/"+instance.name+"/named.conf.options"}, verbose=False) == 1:
        return 1

    if restart_service(instance, {"service":"bind9"}, verbose=False) == 1:
        return 1
    if verbose:
        print(Fore.GREEN+ "      Service bind9 has been installed and configured successfully!"+Style.RESET_ALL)
    return 0

def dns_resolve_name(instance: object, arg: dict, verbose: bool=True) -> int:
    """ Add an association between an ip address and a domain name.
    Args:
        instance (object): This argmument define the lxc instance.
        arg (dict of str: Optional): This argument list maps arguments and their value.
            {
                domain_name (str): This argument is the domain name who will be associated with an ip.
                ns (str): This argument specify the domain name of the DNS authority server for this domain.
                ip_resolution (str): This argument is the ip associated to the domain name.
                mail (str): This argument specify if a MX record must be assigned to this domain name. 'true' value if yes, anyone else if false.
                alias (list of str): This argument is a list of domaine name that are redirected to the domain name specified in yhe value 'domain_name'.

            }
        verbose (bool, optional): This argument define if the function prompt some informations during his execution. Default to True.

    Returns:
        int: Return 1 if the function works successfully, otherwise 0.
    """
    install(instance, {"module":"dnsutils"}, verbose=False)
    # db config
    resolution_file = open("simulation/workstations/"+instance.name+"/db."+arg["domain_name"], "w")
    resolution_file.write("$TTL       604800\n")
    resolution_file.write("@       IN      SOA     "+ arg["ns"] +". admin."+ arg["domain_name"] +". (\n")
    resolution_file.write("                                 3       ;     Serial\n")
    resolution_file.write("                            604800       ;     Refresh\n")
    resolution_file.write("                             86400       ;     Retry\n")
    resolution_file.write("                           2419200       ;     Expire\n")
    resolution_file.write("                            604800   )   ;     Negative Cache TTL\n")

    resolution_file.write(";\n")
    resolution_file.write("; name servers - NS records\n")

    resolution_file.write("@        IN      NS      "+ arg["ns"]+".\n")
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

    #db.inverse
    resolution_inverse_file = open("simulation/workstations/"+instance.name+"/db."+inverse_ip(arg["ip_resolution"])+".in-addr.arpa", "w")
    resolution_inverse_file.write("$TTL       604800\n")
    resolution_inverse_file.write("@       IN      SOA     "+ arg["ns"] +". admin."+ arg["domain_name"] +". (\n")
    resolution_inverse_file.write("                                 3       ;     Serial\n")
    resolution_inverse_file.write("                            604800       ;     Refresh\n")
    resolution_inverse_file.write("                             86400       ;     Retry\n")
    resolution_inverse_file.write("                           2419200       ;     Expire\n")
    resolution_inverse_file.write("                            604800   )   ;     Negative Cache TTL\n")
    resolution_inverse_file.write("@        IN      NS      localhost.\n")
    resolution_inverse_file.write("         IN      PTR     "+arg["domain_name"]+".\n")
    if arg["alias"] != [""]:
        for alias in arg["alias"]:
            resolution_inverse_file.write("         IN      PTR     "+alias+"."+arg["domain_name"]+".\n")
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
