from colorama import Fore, Style
from .logic_actions_utils import install, upload_file, restart_service

################################################

################################################
def inverse_ip(ip):
    tmp = ip.split(".")
    tmp.reverse()
    ip_inverse = tmp[:-1]
    return ".".join(tmp)

def add_zone_named_conf(client,instance,db_filename, verbose=True):
    resolution_file = open("simulation/workstations/"+instance.name+"/named.conf.local", "a+")
    resolution_file.write("zone \""+ db_filename +"\" {\n")
    resolution_file.write("type master;\n")
    resolution_file.write("file \"/etc/bind/db."+db_filename+"\";\n")
    resolution_file.write("};\n")
    resolution_file.close()
    upload_file(client,instance,{"instance_path":"/etc/bind/named.conf.local","host_manager_path":"simulation/workstations/"+instance.name+"/named.conf.local"}, verbose=False)

def dns_installation(client, instance, arg, verbose=True):
    install(client,instance,{"module":"bind9"}, verbose=False)
    dns_resolve_name(client,instance,{"domain_name":arg["domain_name"],"ip_resolution":arg["ip_resolution"],"mail":"","alias":""}, verbose=False)
    instance.execute(["chmod", "+r", "/etc/bind/named.conf.local"])
    restart_service(client,instance,{"service":"bind9"}, verbose=False)

def dns_resolve_name(client, instance, arg, verbose=True):
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
    add_zone_named_conf(client,instance, arg["domain_name"])

    upload_file(client, instance, {"instance_path":"/etc/bind/db."+arg["domain_name"],"host_manager_path":"simulation/workstations/"+instance.name+"/db."+arg["domain_name"]}, verbose=False)
    # instance.files.put("/etc/bind/db."+arg["domain_name"], open("simulation/workstations/"+instance.name+"/db."+arg["domain_name"]).read())
    instance.execute(["chmod", "+r", "/etc/bind/db."+arg["domain_name"]])

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
    upload_file(client,instance,{"instance_path":"/etc/bind/db."+inverse_ip(arg["ip_resolution"])+".in-addr.arpa","host_manager_path":"simulation/workstations/"+instance.name+"/db."+inverse_ip(arg["ip_resolution"])+".in-addr.arpa"}, verbose=False)
    # instance.files.put("/etc/bind/db."+inverse_ip(arg["ip_resolution"])+".in-addr.arpa", open("simulation/workstations/"+instance.name+"/db."+inverse_ip(arg["ip_resolution"])+".in-addr.arpa").read())
    
    # named.conf.local
    add_zone_named_conf(client,instance, inverse_ip(arg["ip_resolution"])+".in-addr.arpa", verbose=False)
    instance.execute(["chmod", "+r", "/etc/bind/db."+inverse_ip(arg["ip_resolution"])+".in-addr.arpa"])

    instance.execute(["chmod", "+r", "/etc/bind/named.conf.local"])
    restart_service(client,instance,{"service":"bind9"}, verbose=False)
    
    result = instance.execute(["nslookup",arg["domain_name"],"127.0.0.1"])
    if "SERVFAIL" in result:
        print( Fore.RED+"      Error during adding new resolution name"+Style.RESET_ALL )
    else:
        if verbose:
            print( Fore.GREEN+"      New resolution file for "+arg["domain_name"]+" and bind9 service have been restarted!"+Style.RESET_ALL )
    
    result = instance.execute(["nslookup",arg["ip_resolution"],"127.0.0.1"])
    if "SERVFAIL" in result:
        print( Fore.RED+"      Error during adding new inverse resolution name"+Style.RESET_ALL )
    else:
        if verbose:
            print( Fore.GREEN+"      New inverse resolution file for "+arg["ip_resolution"]+" and bind9 service have been restarted!"+Style.RESET_ALL )
