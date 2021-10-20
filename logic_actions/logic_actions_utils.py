import os
import re
import time
import json
import random
import hashlib
import OpenSSL.crypto as crypto
from colorama import Fore, Style

# Review
def load_json_file(path_conf):
    with open(path_conf, "r") as f:
        conf_physic = json.load(f)
    return conf_physic

# Review
def dump_json_file(dict_object, path_conf):
    with open(path_conf, "w") as f:
        json.dump(dict_object, f)
    return 

# Review
def update(client, instance, arg, verbose=True):
    instance.execute(["rm", "-rf", "/var/lib/apt/lists/*"])
    result = instance.execute(["apt-get", "-y", "update"])
    if result.exit_code == 0:
        if verbose:
            print( Fore.GREEN + "      Update has been done! "+ Style.RESET_ALL )
    else:
        print( Fore.RED + "      Update failed! "+ Style.RESET_ALL )

def execute_raw_command(client, instance, arg, verbose=True):
    result = instance.execute(arg["command"].split())
    if result.exit_code == 0:

        print( Fore.GREEN + "      Exit_code: [ "+str(result.exit_code)+" ]"+ Style.RESET_ALL )
        print( Fore.GREEN + "      Stdout: [ "+result.stdout+" ]"+ Style.RESET_ALL )
    else:
        print( Fore.RED + "      Exit_code: [ "+str(result.exit_code)+" ]"+ Style.RESET_ALL )
        print( Fore.RED + "      Error: [ "+result.stderr+" ]"+ Style.RESET_ALL )

# Review
def upload_file(client, instance, arg, verbose=True):
    instance.files.put(arg["instance_path"], open(arg["host_manager_path"]).read())
    result = instance.execute(["ls", arg["instance_path"]])
    if result.stderr:
        print( Fore.RED + "      Upload failed!"+ Style.RESET_ALL )
    else:
        if verbose:
            print( Fore.GREEN + "      File [ "+arg["instance_path"]+" ] wad uploaded!"+ Style.RESET_ALL )

def download_file(client, instance, arg, verbose=True):
    print( Fore.YELLOW +"In progress..."+ Style.RESET_ALL)

def delete_file(client, instance, arg, verbose=True):
    if instance.files.delete_available():
        instance.files.delete(arg["instance_path"])
        result = instance.execute(["ls", arg["instance_path"]])
        if result.stderr:
            if verbose:
                print( Fore.GREEN+ "      File [ "+arg["instance_path"]+" ] has been deleted!" +Style.RESET_ALL )
    else:
        print( Fore.RED+ "      File was not deleted..." +Style.RESET_ALL )

# Review
def install(client, instance, arg, verbose=True):
    result = instance.execute(["apt", "list", arg["module"]])
    if (arg["module"] in result.stdout) and ("installed" in result.stdout):
        if verbose:
            print( Fore.YELLOW + "      Module "+arg["module"]+" is already installed!" + Style.RESET_ALL )
    else:
        update(client,instance,{"":""}, verbose=False)
        instance.execute(["apt-get", "install", "-y", arg["module"]])
        result = instance.execute(["apt", "list", arg["module"]])
        if (arg["module"] in result.stdout) and ("installed" in result.stdout):
            if verbose:
                print( Fore.GREEN + "      Module "+arg["module"]+" has been installed !" + Style.RESET_ALL )
        else:
            print( Fore.RED + "      Error during installation module:"+arg["module"]+"  ["+result.stderr+"]" + Style.RESET_ALL )

# Review
def install_python_packages(client,instance,arg, verbose=True):
    install(client,instance,{"module":"python3-pip"}, verbose=False)

    result = instance.execute(["pip3","show",arg["package"]]).stdout
    if result == "":
        instance.execute(["pip3","install",arg["package"]])
        result = instance.execute(["pip3","show",arg["package"]]).stdout
        if result != "":
            if verbose:
                print( Fore.GREEN + "      Package "+arg["package"]+" has been installed !" + Style.RESET_ALL )
        else:
            print( Fore.RED + "      Error during package "+arg["package"]+" installation!" + Style.RESET_ALL )
    else:
        if verbose:
            print( Fore.YELLOW + "      Package "+arg["package"]+" already installed !" + Style.RESET_ALL )

# Review
def create_local_user(client, instance, arg, verbose=True):
    password = hashlib.md5(arg["password"].encode())
    instance.execute(["useradd","-s","/bin/bash","-m","-p",str(password),arg["username"]])
    if arg["username"] in instance.execute(["cat","/etc/passwd"]).stdout.split("\n")[-2]:
        if verbose:
            print( Fore.GREEN + "      User "+arg["username"]+" was created!" + Style.RESET_ALL )
    else:
        print( Fore.RED + "      Error during user creation" + Style.RESET_ALL )

def add_user2group(client, instance, arg, verbose=True):
    instance.execute(["usermod","-a","-G", arg["group_name"], arg["username"]])
    result = instance.execute(["getent","group",arg["group_name"]])
    if arg["username"] in result.stdout:
        if verbose:
            print( Fore.GREEN + "      User "+arg["username"]+" has been added to "+arg["group_name"]+"!" + Style.RESET_ALL )
    else:
        print( Fore.RED + "      Error user "+arg["username"]+" was not added to new group..." + Style.RESET_ALL )

def change_fileorfolder_user_owner(client, instance, arg, verbose=True):
    instance.execute(["chown", "-R", arg["new_owner"],arg["file_path"]])
    result = instance.execute(["ls","-la",arg["file_path"]])
    if arg["new_owner"] in result.stdout:
        if verbose:
            print( Fore.GREEN + "      "+arg["new_owner"]+"is the new owner of "+arg["file_path"]+"!"+ Style.RESET_ALL )
    else:
        print( Fore.RED + "      Error during file owner changing..." + Style.RESET_ALL )

def change_fileorfolder_group_owner(client, instance, arg, verbose=True):
    result = instance.execute(["stats","-c","%G",arg["fileorfolder_path"]])
    if arg["new_group"] not in result.stdout:
        instance.execute(["chgrp","-R",arg["new_group"],arg["fileorfolder_path"]])
        result = instance.execute(["stat","-c","%G",arg["fileorfolder_path"]])
        if arg["new_group"] in result.stdout:
            if verbose:
                print( Fore.GREEN + "      Group "+arg["new_group"]+" has been added to "+arg["fileorfolder_path"]+"!" + Style.RESET_ALL )
        else:
            print( Fore.RED + "      Error group "+arg["new_group"]+" was not added to "+arg["fileorfolder_path"]+"..." + Style.RESET_ALL )
    else:
        if verbose:
            print( Fore.YELLOW +"      "+ arg["fileorfolder_path"] +" is already in group "+ arg["new_group"] +Style.RESET_ALL )

def create_local_group(client, instance, arg, verbose=True):
    result = instance.execute(["cat","/etc/group"])
    if arg["new_group"] in result.stdout:
        if verbose:
            print(Fore.YELLOW+"      "+arg["new_group"]+" group has already created" +Style.RESET_ALL)
    else:
        instance.execute(["groupadd",arg["new_group"]])
        result = instance.execute(["cat","/etc/group"])
        if arg["new_group"] in result.stdout:
            if verbose:
                print(Fore.GREEN+"      "+arg["new_group"]+ " group was created" +Style.RESET_ALL)
        else:
            print(Fore.RED+ "      Error during "+arg["new_group"]+" group creation..." +Style.RESET_ALL)
# Review
def upgrade(client, instance, arg, verbose=True):
    instance.execute(["apt-get", "-y", "upgrade"])
    if result.exit_code == 0:
        if verbose:
            print(ore.GREEN+"      Upgrade!"+Style.RESET_ALL)
    else:
        print(Fore.RED+"      Upgrade failed"+Style.RESET_ALL)

def add_apt_repository(client, instance, arg, verbose=True):
    result = instance.execute(["add-apt-repository", arg["ppa_repository"]])
    print( "      Add repository "+str(result.exit_code) )

# Review
def restart_service(client, instance, arg, verbose=True):
    instance.execute(["systemctl", "restart", arg["service"]])
    result = instance.execute(["systemctl", "status", arg["service"]])
    if "Active: active" in result.stdout:
        if verbose:
            print( Fore.GREEN+ "      "+arg["service"]+" is running!"+Style.RESET_ALL )
    else:
        print( Fore.RED+ "      "+arg["service"]+" is not running!"+Style.RESET_ALL )

# Review
def add_nameserver(client, instance, arg, verbose=True):
    resolveconf = open("simulation/workstations/"+instance.name+"/tmp-resolved.conf", "a+")
    resolveconf.write("nameserver "+arg["nameserver_ip"]+"\n")
    resolveconf.close()
    time.sleep(1)
    upload_file(client, instance, {"instance_path":"/etc/resolv.conf","host_manager_path":"simulation/workstations/"+instance.name+"/tmp-resolved.conf"}, verbose=False)

    result = instance.execute(["cat","/etc/resolv.conf"]).stdout
    if  arg["nameserver_ip"] in result:
        if verbose:
            print( Fore.GREEN +"      "+ arg["nameserver_ip"]+" has been added to nameserver list!" + Style.RESET_ALL )
    else:
        print( Fore.RED + "      Error durind adding nameserver" + Style.RESET_ALL )

def clear_nameserver(client, instance, arg, verbose=True):
    try:
        if instance.files.delete_available():
            instance.files.delete("/etc/resolv.conf")

        os.remove("simulation/workstations/"+instance.name+"/tmp-resolved.conf")
        resolveconf = open("simulation/workstations/"+instance.name+"/tmp-resolved.conf", "a+")
        resolveconf.close()
        instance.files.put('/etc/resolv.conf', open("simulation/workstations/"+instance.name+"/tmp-resolved.conf").read())
        if verbose:
            print( Fore.GREEN + "      Resolv.conf file is clear!" + Style.RESET_ALL )
    except:
        print( Fore.RED + "      Resolv.conf file can't be clear" + Style.RESET_ALL )

def push_sim_user(client, instance, arg, verbose=True):
    conf_tmp = load_json_file("simulation/Configurations/conf_sim.json")
    users_dict = {}
    users_list = []

    create_local_group(client, instance, {"new_group":"simulation"}, verbose=False)

    instance.execute(["mkdir","/tmp/Documents/"])
    change_fileorfolder_group_owner(client,instance,{"fileorfolder_path":"/tmp/Documents/","new_group":"simulation"}, verbose=False)
    instance.execute(["chmod","770","-R","/tmp/Documents/"])

    for workstation in conf_tmp["workstations"]:
        if workstation["hostname"] == instance.name:
            for user in workstation["users"]:
                users_list.append(user)
                add_user2group(client, instance, {"username":user["name"],"group_name":"simulation"}, verbose=False)

    users_dict["users"] = users_list
    dump_json_file(users_dict, "simulation/workstations/"+instance.name+"/users.json")

    install(client,instance,{"module":"firefox"}, verbose=False)
    install_python_packages(client,instance,{"package":"bs4"}, verbose=False)
    install_python_packages(client,instance,{"package":"pysmb"}, verbose=False)
    install_python_packages(client,instance,{"package":"selenium"}, verbose=False)
    install_python_packages(client,instance,{"package":"essential-generators"}, verbose=False)

    instance.files.recursive_put("sim_user","/tmp/sim_user")
    upload_file(client, instance, {"instance_path":"/tmp/sim_user/users.json","host_manager_path":"simulation/workstations/"+instance.name+"/users.json"}, verbose=False)
    change_fileorfolder_group_owner(client, instance, {"new_group":"simulation","fileorfolder_path":"/tmp/sim_user"}, verbose=False)
    instance.execute(["chmod","-R","g+rwx","/tmp/sim_user"])

def configure_iptables(client, instance, arg, verbose=True):
    install(client, instance, {"module":"ulogd2"}, verbose=False)

    instance.execute(["iptables","-A","INPUT","-i","eth1","-p","tcp","-m","state","--state","NEW","-j","NFLOG","--nflog-prefix","[iptables]"])
    instance.execute(["iptables","-A","OUTPUT","-o","eth1","-p","tcp","-m","state","--state","NEW","-j","NFLOG","--nflog-prefix","[iptables]"])
    instance.execute(["iptables","-A","INPUT","-i","eth1","-p","tcp","-m","state","--state","NEW","-j","NFLOG","--nflog-prefix","[iptables]"])
    instance.execute(["iptables","-A","OUTPUT","-o","eth1","-p","tcp","-m","state","--state","NEW","-j","NFLOG","--nflog-prefix","[iptables]"])

def flush_iptables(client, instance, arg, verbose=True):
    instance(["iptables","-F"])

################
# CERTIFICATES #
################

###### CA certificate 
def generate_root_ca(client, instance, arg, verbose=True):
    os.makedirs("simulation/workstations/"+instance.name+"/ca/"+arg["private_key_ca_certificate_name"], exist_ok=True)

    ###### Generate key
    ca_key = crypto.PKey()
    ca_key.generate_key(crypto.TYPE_RSA, int(arg["bits"]))

    ###### Generate certificate
    ca_cert = crypto.X509()
    ca_cert.set_version(int(arg["version"]))
    if arg["serial"] != "":
        ca_cert.set_serial_number(random.randint(50000000,100000000))
    ca_subj = ca_cert.get_subject()
    ca_subj.countryName = arg["C"]
    ca_subj.stateOrProvinceName = arg["ST"]
    ca_subj.localityName = arg["L"]
    ca_subj.organizationName = arg["O"]
    ca_subj.commonName = arg["CN"]
    ca_cert.set_issuer(ca_subj)
    ca_cert.set_pubkey(ca_key)
    ca_cert.gmtime_adj_notBefore(0)
    ca_cert.gmtime_adj_notAfter(int(arg["days_validity"])*24*60*60)

    ca_cert.add_extensions([
        crypto.X509Extension(b"subjectKeyIdentifier",False,b"hash",subject=ca_cert)
    ])
    ca_cert.add_extensions([
        crypto.X509Extension(b"basicConstraints",False,b"CA:TRUE"),
        crypto.X509Extension(b"keyUsage",False,b"keyCertSign,cRLSign")
    ])

    ca_cert.sign(ca_key, "sha256")

    ###### Dump certificate
    with open("simulation/workstations/"+instance.name+"/ca/"+arg["private_key_ca_certificate_name"]+"/"+arg["private_key_ca_certificate_name"]+".cert", "wt") as f:
        f.write(crypto.dump_certificate(crypto.FILETYPE_PEM, ca_cert).decode("utf-8"))

    ###### Dump key
    with open("simulation/workstations/"+instance.name+"/ca/"+arg["private_key_ca_certificate_name"]+"/"+arg["private_key_ca_certificate_name"]+".key", "wt") as f:
        f.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, ca_key).decode("utf-8"))

    ###### Create directory
    instance.execute(["mkdir", "/ca"])
    instance.execute(["mkdir", "/ca/"+arg["private_key_ca_certificate_name"]])

    upload_file(client, instance, {"instance_path":"/ca/"+arg["private_key_ca_certificate_name"]+"/"+arg["private_key_ca_certificate_name"]+".key", "host_manager_path": "simulation/workstations/"+instance.name+"/ca/"+arg["private_key_ca_certificate_name"]+"/"+arg["private_key_ca_certificate_name"]+".key"}, verbose=False)
    upload_file(client, instance, {"instance_path":"/ca/"+arg["private_key_ca_certificate_name"]+"/"+arg["private_key_ca_certificate_name"]+".cert", "host_manager_path": "simulation/workstations/"+instance.name+"/ca/"+arg["private_key_ca_certificate_name"]+"/"+arg["private_key_ca_certificate_name"]+".cert"}, verbose=False)

###### Middle certificate 
def generate_middle_certificates(client, instance, arg, verbose=True):
    os.makedirs("simulation/workstations/"+instance.name+"/middle_cert/"+arg["private_key_middle_certificate_name"], exist_ok=True)
    ###### Load CA
    ca_key = open("simulation/workstations/"+arg["ca_holder"]+"/ca/"+arg["ca_name"]+"/"+arg["ca_name"]+".key").read()
    ca_key = crypto.load_privatekey(crypto.FILETYPE_PEM, ca_key)
    ca_cert = open("simulation/workstations/"+arg["ca_holder"]+"/ca/"+arg["ca_name"]+"/"+arg["ca_name"]+".cert").read()
    ca_cert = crypto.load_certificate(crypto.FILETYPE_PEM, ca_cert)

    ##### Generate private key
    middle_key = crypto.PKey()
    middle_key.generate_key(crypto.TYPE_RSA, int(arg["bits"]))

    ##### Generate certificate
    middle_cert = crypto.X509()
    middle_cert.set_version(int(arg["version"]))
    if arg["serial"] != "":
        middle_cert.set_serial_number(arg["serial"])
    else:
        middle_cert.set_serial_number(random.randint(50000000,100000000))
    middle_subj = middle_cert.get_subject()
    middle_subj.countryName = arg["C"]
    middle_subj.stateOrProvinceName = arg["ST"]
    middle_subj.localityName = arg["L"]
    middle_subj.organizationName = arg["O"]
    middle_subj.commonName = arg["CN"]
    middle_cert.gmtime_adj_notBefore(0)
    middle_cert.gmtime_adj_notAfter(int(arg["days_validity"])*24*60*60)

    middle_cert.set_issuer(ca_cert.get_subject())

    middle_cert.add_extensions([
        crypto.X509Extension(b"subjectKeyIdentifier",False,b"hash",subject=middle_cert)
    ])
    middle_cert.add_extensions([
        crypto.X509Extension(b"authorityKeyIdentifier",False,b"keyid:always", issuer=ca_cert),
        crypto.X509Extension(b"basicConstraints",False,b"CA:TRUE"),
        crypto.X509Extension(b"keyUsage",False,b"keyCertSign, cRLSign")
    ])

    middle_cert.set_pubkey(middle_key)
    middle_cert.sign(ca_key, "sha256")

    # Verify certificate chain
    store = crypto.X509Store()
    store.add_cert(ca_cert)
    ctx = crypto.X509StoreContext(store, middle_cert)
    if ctx.verify_certificate() == None:
        if verbose:
            print( Fore.GREEN + "      Certificate chain is working!" + Style.RESET_ALL )
    else:
        print( Fore.RED + "      Failed during certificate generation..." + Style.RESET_ALL )


    # Dump middle certificate
    with open("simulation/workstations/"+instance.name+"/middle_cert/"+arg["private_key_middle_certificate_name"]+"/"+arg["private_key_middle_certificate_name"]+".cert", "wt") as f:
        f.write(crypto.dump_certificate(crypto.FILETYPE_PEM, middle_cert).decode("utf-8"))

    # Dump middle key
    with open("simulation/workstations/"+instance.name+"/middle_cert/"+arg["private_key_middle_certificate_name"]+"/"+arg["private_key_middle_certificate_name"]+".key", "wt") as f:
        f.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, middle_key).decode("utf-8"))

    ###### Create directory
    instance.execute(["mkdir", "/middle_cert"])
    instance.execute(["mkdir", "/middle_cert/"+arg["private_key_middle_certificate_name"]])
    instance.execute(["mkdir", "/middle_cert/"+arg["private_key_middle_certificate_name"]+"/"])

    upload_file(client, instance, {"instance_path":"/middle_cert/"+arg["private_key_middle_certificate_name"]+"/"+arg["private_key_middle_certificate_name"]+".key", "host_manager_path": "simulation/workstations/"+instance.name+"/middle_cert/"+arg["private_key_middle_certificate_name"]+"/"+arg["private_key_middle_certificate_name"]+".key"}, verbose=False)
    upload_file(client, instance, {"instance_path":"/middle_cert/"+arg["private_key_middle_certificate_name"]+"/"+arg["private_key_middle_certificate_name"]+".cert", "host_manager_path": "simulation/workstations/"+instance.name+"/middle_cert/"+arg["private_key_middle_certificate_name"]+"/"+arg["private_key_middle_certificate_name"]+".cert"}, verbose=False)
    upload_file(client, instance, {"instance_path":"/middle_cert/"+arg["private_key_middle_certificate_name"]+"/"+arg["ca_name"]+".cert", "host_manager_path": "simulation/workstations/"+arg["ca_holder"]+"/ca/"+arg["ca_name"]+"/"+arg["ca_name"]+".cert"}, verbose=False)

###### Certificate 
def generate_certificates(client, instance, arg, verbose=True):
    os.makedirs("simulation/workstations/"+instance.name+"/cert/"+arg["private_key_certificate_name"], exist_ok=True)

    ##### Load middle certificate 
    middle_key = open("simulation/workstations/"+arg["middle_holder"]+"/middle_cert/"+arg["middle_name"]+"/"+arg["middle_name"]+".key").read()
    middle_key = crypto.load_privatekey(crypto.FILETYPE_PEM, middle_key)
    middle_cert = open("simulation/workstations/"+arg["middle_holder"]+"/middle_cert/"+arg["middle_name"]+"/"+arg["middle_name"]+".cert").read()
    middle_cert = crypto.load_certificate(crypto.FILETYPE_PEM, middle_cert)

    ##### Generate private key
    client_key = crypto.PKey()
    client_key.generate_key(crypto.TYPE_RSA, int(arg["bits"]))

    ##### Generate certificate
    client_cert = crypto.X509()
    client_cert.set_version(int(arg["version"]))
    if arg["serial"] != "":
        client_cert.set_serial_number(arg["serial"])
    else:
        client_cert.set_serial_number(random.randint(50000000,100000000))
    client_subj = client_cert.get_subject()
    client_subj.countryName = arg["C"]
    client_subj.stateOrProvinceName = arg["ST"]
    client_subj.localityName = arg["L"]
    client_subj.organizationName = arg["O"]
    client_subj.commonName = arg["CN"]
    client_cert.gmtime_adj_notBefore(0)
    client_cert.gmtime_adj_notAfter(int(arg["days_validity"])*24*60*60)

    client_issuer = middle_cert.get_subject()
    client_cert.set_issuer(client_issuer)

    client_cert.add_extensions([
        crypto.X509Extension(b"subjectKeyIdentifier",False,b"hash",subject=client_cert)
    ])
    client_cert.add_extensions([
        crypto.X509Extension(b"authorityKeyIdentifier",False,b"keyid:always", issuer=middle_cert),
        crypto.X509Extension(b"subjectAltName",False,b"DNS:"+arg["dns"].encode("utf-8"))
        # crypto.X509Extension(b"extendKeyUsage",False,b"serverAuth")
    ])

    client_cert.set_pubkey(client_key)
    client_cert.sign(middle_key, "sha256")

    # Verify certificate chain
    store = crypto.X509Store()
    store.add_cert(middle_cert)
    store.add_cert(crypto.load_certificate(crypto.FILETYPE_PEM, open("simulation/workstations/"+arg["ca_holder"]+"/ca/"+arg["ca_name"]+"/"+arg["ca_name"]+".cert").read()))
    ctx = crypto.X509StoreContext(store, client_cert)
    if ctx.verify_certificate() == None:
        if verbose:
            print( Fore.GREEN + "      Certificate chain is working!" + Style.RESET_ALL )
    else:
        print( Fore.RED + "      Failed during certificate generation..." + Style.RESET_ALL )


    # Dump certificate
    with open("simulation/workstations/"+instance.name+"/cert/"+arg["private_key_certificate_name"]+"/"+arg["private_key_certificate_name"]+".cert", "wt") as f:
        f.write(crypto.dump_certificate(crypto.FILETYPE_PEM, client_cert).decode("utf-8"))

    # Dump key
    with open("simulation/workstations/"+instance.name+"/cert/"+arg["private_key_certificate_name"]+"/"+arg["private_key_certificate_name"]+".key", "wt") as f:
        f.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, client_key).decode("utf-8"))

    ###### Create directory
    instance.execute(["mkdir", "/certs"])
    instance.execute(["mkdir", "/certs/"+arg["private_key_certificate_name"]])
    
    upload_file(client, instance, {"instance_path":"/certs/"+arg["private_key_certificate_name"]+"/"+arg["private_key_certificate_name"]+".key", "host_manager_path": "simulation/workstations/"+instance.name+"/cert/"+arg["private_key_certificate_name"]+"/"+arg["private_key_certificate_name"]+".key"}, verbose=False)
    upload_file(client, instance, {"instance_path":"/certs/"+arg["private_key_certificate_name"]+"/"+arg["private_key_certificate_name"]+".cert", "host_manager_path": "simulation/workstations/"+instance.name+"/cert/"+arg["private_key_certificate_name"]+"/"+arg["private_key_certificate_name"]+".cert"}, verbose=False)
    upload_file(client, instance, {"instance_path":"/certs/"+arg["private_key_certificate_name"]+"/"+arg["middle_name"]+".cert", "host_manager_path": "simulation/workstations/"+arg["middle_holder"]+"/middle_cert/"+arg["middle_name"]+"/"+arg["middle_name"]+".cert"}, verbose=False)
    upload_file(client, instance, {"instance_path":"/certs/"+arg["private_key_certificate_name"]+"/"+arg["ca_name"]+".cert", "host_manager_path": "simulation/workstations/"+arg["ca_holder"]+"/ca/"+arg["ca_name"]+"/"+arg["ca_name"]+".cert"}, verbose=False)
