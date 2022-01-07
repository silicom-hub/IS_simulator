""" This file contains help function for other high level logic actions """
import os
import cv2
import time
import json
import random
import hashlib
import subprocess
import OpenSSL.crypto as crypto
from colorama import Fore, Style

def load_json_file(path_conf):
    """ Loads a json file specified in the path """
    with open(path_conf, "r") as file_conf:
        conf_physic = json.load(file_conf)
    return conf_physic

def dump_json_file(dict_object, path_conf):
    """ Pull an object json file to the simulation's host specified in path_conf """
    with open(path_conf, "w") as file_conf:
        json.dump(dict_object, file_conf)

def save_nameserver_ip(instance, filepath="/etc/resolv.conf"):
    """ Save ip in /etc/resolv.conf in a list """
    nameservers_ip = []
    nameservers = instance.execute(["cat", filepath]).stdout.split("\n")
    for nameserver in nameservers:
        nameserver = nameserver.split(" ")
        if len(nameserver) == 2 and nameserver[0] == "nameserver":
            nameservers_ip.append(nameserver[1])
    return nameservers_ip

def update(instance, verbose=True):
    """ Downloads package lists from the repositories and to get information about
    the latest version of packages and their dependencies on the remote instance """
    execute_command(instance, {"command":["rm", "-rf", "/var/lib/apt/lists/*"], "expected_exit_code":"0"}, verbose=False)
    result = execute_command(instance, {"command":["apt-get", "-y", "update"], "expected_exit_code":"0"}, verbose=False)
    if result.exit_code == 0:
        if verbose:
            print(Fore.GREEN + "      Update has been done!"+ Style.RESET_ALL)
        return 0
    print(Fore.RED + "      Update failed!"+ Style.RESET_ALL)
    return 1

def create_execute_command_remote_bash(instance, arg, verbose=False):
    nameserver_ips = save_nameserver_ip(instance)
    add_nameserver(instance, {"nameserver_ip":"8.8.8.8"}, verbose=False)
    remote_file = open("simulation/workstations/"+instance.name+"/"+arg["script_name"], "w")
    remote_file.write("#!/bin/bash\n")
    for command in arg["commands"]:
        remote_file.write(command+"\n")
    remote_file.close()
    if upload_file(instance, {"instance_path":"/root/"+arg["script_name"], "host_manager_path":"simulation/workstations/"+instance.name+"/"+arg["script_name"]}, verbose=False):
        return 1  
    change_permission(instance, {"file_path":"/root/"+arg["script_name"], "owner":"7", "group":"7", "other":"7"}, verbose=False)
    execute_command(instance, {"command":["./"+arg["script_name"]], "expected_exit_code":"0"}, verbose=False)
    if arg["delete"] == "true":
        if delete_file(instance, {"instance_path":"/root/"+arg["script_name"]}, verbose=False) == 1:
            return 1
    clear_nameserver(instance, verbose=False)
    for nameserver_ip in nameserver_ips:
        add_nameserver(instance, {"nameserver_ip":nameserver_ip}, verbose=False)
    return 0

def execute_command(instance, arg, verbose=True):
    """ Execute the command line specified in the remote instance """
    result = instance.execute(arg["command"])
    if result.exit_code == int(arg["expected_exit_code"]):
        if verbose:
            print(Fore.GREEN + "      Command: [ "+" ".join(arg["command"])+" ]"+ Style.RESET_ALL)
            print(Fore.GREEN + "      Exit_code: [ "+str(result.exit_code)+" ]"+ Style.RESET_ALL)
            print(Fore.GREEN + "      Stdout: [ "+result.stdout+" ]"+ Style.RESET_ALL)
            print(Fore.GREEN + "      Stderr: [ "+result.stderr+" ]"+ Style.RESET_ALL)
        return result
    print(Fore.RED + "      Command: [ "+" ".join(arg["command"])+" ]"+ Style.RESET_ALL)
    print(Fore.RED + "      Exit_code: [ "+str(result.exit_code)+" ]"+ Style.RESET_ALL)
    print(Fore.RED + "      Stdout: [ "+result.stdout+" ]"+ Style.RESET_ALL)
    print(Fore.RED + "      Stderr: [ "+result.stderr+" ]"+ Style.RESET_ALL)
    execute_raw_command(instance, {"command":" ".join(arg["command"])}, verbose=False)
    return result

def execute_raw_command(instance, arg, verbose=True):
    """ Execute the command line specified in the remote instance """
    result = instance.raw_interactive_execute([arg["command"]])
    if verbose:
        print(Fore.GREEN + str(result) + Style.RESET_ALL)
    return result

def upload_file(instance, arg, verbose=True):
    """ Upload file specified in arg on the remote instance """
    instance.files.put(arg["instance_path"], open(arg["host_manager_path"]).read())
    result = execute_command(instance, {"command":["ls", arg["instance_path"]], "expected_exit_code":"0"}, verbose=False)
    if result.stderr:
        print(Fore.RED + "      Upload failed!"+ Style.RESET_ALL)
        return 1
    if verbose:
        print(Fore.GREEN + "      File [ "+arg["instance_path"]+" ] wad uploaded!"+ Style.RESET_ALL)
    return 0

def download_file(instance, arg, verbose=True):
    """ Get file specified in arg on the remote instance to the simulation's host """
    file = open(arg["host_manager_path"], "wb")
    print(instance.files.get(arg["instance_path"]))
    print(type(instance.files.get(arg["instance_path"])))
    file.write(instance.files.get(arg["instance_path"]))
    file.close()
    if verbose:
        print(Fore.GREEN + "      File [ "+arg["instance_path"]+" ] wad uploaded!"+ Style.RESET_ALL)
    return 0

def delete_file(instance, arg, verbose=True):
    """ Delete file specified in arg on the remote instance """
    if instance.files.delete_available():
        instance.files.delete(arg["instance_path"])
        result = execute_command(instance, {"command":["ls", arg["instance_path"]], "expected_exit_code":"2"}, verbose=False)
        if result.stderr:
            if verbose:
                print(Fore.GREEN+ "      File [ "+arg["instance_path"]+" ] has been deleted!" +Style.RESET_ALL)
            return 0
        print(Fore.RED+ "      File was not deleted..." +Style.RESET_ALL)
        return 1
    print(Fore.RED+ "      File was not deleted..." +Style.RESET_ALL)
    return 1

def install(instance, arg, verbose=True):
    """ Install package specified in arg on the remote instance """
    nameserver_ips = save_nameserver_ip(instance)
    clear_nameserver(instance, verbose=False)
    add_nameserver(instance, {"nameserver_ip":"8.8.8.8"}, verbose=False)
    result = execute_command(instance, {"command":["apt", "list", arg["module"]], "expected_exit_code":"0"}, verbose=False)
    if (arg["module"] in result.stdout) and ("installed" in result.stdout):
        if verbose:
            print(Fore.YELLOW + "      Module "+arg["module"]+" is already installed!" + Style.RESET_ALL)
        clear_nameserver(instance, verbose=False)
        for nameserver_ip in nameserver_ips:
            add_nameserver(instance, {"nameserver_ip":nameserver_ip}, verbose=False)
        return 0
    update(instance, verbose=False)
    execute_command(instance, {"command":["apt-get", "install", "-y", arg["module"]], "expected_exit_code":"0"}, verbose=False)
    result = execute_command(instance, {"command":["apt", "list", arg["module"]], "expected_exit_code":"0"}, verbose=False)

    if (arg["module"] in result.stdout) and ("installed" in result.stdout):
        if verbose:
            print(Fore.GREEN + "      Module "+arg["module"]+" has been installed !" + Style.RESET_ALL)
        clear_nameserver(instance, verbose=False)
        for nameserver_ip in nameserver_ips:
            add_nameserver(instance, {"nameserver_ip":nameserver_ip}, verbose=False)
        return 0
    print(Fore.RED + "      Error during installation module:"+arg["module"]+"  ["+result.stderr+"]" + Style.RESET_ALL)
    clear_nameserver(instance, verbose=False)
    for nameserver_ip in nameserver_ips:
        add_nameserver(instance, {"nameserver_ip":nameserver_ip}, verbose=False)
    return 1

def install_python_packages(instance, arg, verbose=True):
    """ Install python3 library specified in arg on the remote instance """
    install(instance, {"module":"python3-pip"}, verbose=False)

    result = execute_command(instance, {"command":["pip3", "show", arg["package"]], "expected_exit_code":"1"}, verbose=False)
    if result.exit_code == 1:
        nameserver_ips = save_nameserver_ip(instance)
        clear_nameserver(instance, verbose=False)
        add_nameserver(instance, {"nameserver_ip":"8.8.8.8"}, verbose=False)
        execute_command(instance, {"command":["pip3", "install", arg["package"]], "expected_exit_code":"0"}, verbose=False)
        clear_nameserver(instance, verbose=False)
        for nameserver_ip in nameserver_ips:
            add_nameserver(instance, {"nameserver_ip":nameserver_ip}, verbose=False)
        result = execute_command(instance, {"command":["pip3", "show", arg["package"]], "expected_exit_code":"0"}, verbose=False)
        if result != "":
            if verbose:
                print(Fore.GREEN + "      Package "+arg["package"]+" has been installed !" + Style.RESET_ALL)
            return 0
        print(Fore.RED + "      Error during package "+arg["package"]+" installation!" + Style.RESET_ALL)
        return 1
    if verbose:
        print(Fore.YELLOW + "      Package "+arg["package"]+" already installed !" + Style.RESET_ALL)
    return 1

def wget(instance, arg, verbose=True):
    nameserver_ips = save_nameserver_ip(instance)
    clear_nameserver(instance, verbose=False)
    add_nameserver(instance, {"nameserver_ip":"8.8.8.8"}, verbose=False)
    execute_command(instance, {"command":["wget", "-L", arg["url"], "-P", arg["local_path"]], "expected_exit_code":"0"}, verbose=False)
    clear_nameserver(instance, verbose=False)
    for nameserver_ip in nameserver_ips:
        add_nameserver(instance, {"nameserver_ip":nameserver_ip}, verbose=False)

def create_local_user(instance, arg, verbose=True):
    """ Create a local user with password on the remote instance """
    password = hashlib.md5(arg["password"].encode())
    # execute_command(instance, {"command":"useradd -s /bin/bash -m -p "+str(password)+" "+arg["username"]})
    instance.execute(["useradd", "-s", "/bin/bash", "-m", "-p", str(password), arg["username"]])
    if arg["username"] in instance.execute(["cat", "/etc/passwd"]).stdout.split("\n")[-2]:
        if verbose:
            print(Fore.GREEN + "      User "+arg["username"]+" was created!" + Style.RESET_ALL)
        return 0
    print(Fore.RED + "      Error during user creation" + Style.RESET_ALL)
    return 1

def add_user2group(instance, arg, verbose=True):
    """ Add user on the remote instance in a user group specified in arg """
    execute_command(instance, {"command":["usermod", "-a", "-G", arg["group_name"], arg["username"]], "expected_exit_code":"0"}, verbose=False)
    result = execute_command(instance, {"command":["getent", "group", arg["group_name"]], "expected_exit_code":"0"}, verbose=False)
    if arg["username"] in result.stdout:
        if verbose:
            print(Fore.GREEN + "      User "+arg["username"]+" has been added to "+arg["group_name"]+"!" + Style.RESET_ALL)
        return 0
    print(Fore.RED + "      Error user "+arg["username"]+" was not added to new group..." + Style.RESET_ALL)
    return 1

def change_fileorfolder_user_owner(instance, arg, verbose=True):
    """ Change owner of a file or a folder on the remote instance """
    execute_command(instance, {"command":["chown", "-R", arg["new_owner"], arg["file_path"]], "expected_exit_code":"0"}, verbose=False)
    result = execute_command(instance, {"command":["ls", "-la", arg["file_path"]], "expected_exit_code":"0"}, verbose=False)
    if arg["new_owner"] in result.stdout:
        if verbose:
            print(Fore.GREEN + "      "+arg["new_owner"]+" is the new owner of "+arg["file_path"]+"!"+ Style.RESET_ALL)
        return 0
    print(Fore.RED + "      Error during file owner changing..." + Style.RESET_ALL)
    return 1

def change_fileorfolder_group_owner(instance, arg, verbose=True):
    """ Change group of a file or a folder on the remote instance """
    result = instance.execute(["stats", "-c", "%G", arg["fileorfolder_path"]])
    if arg["new_group"] not in result.stdout:
        execute_command(instance, {"command":["chgrp", "-R", arg["new_group"], arg["fileorfolder_path"]], "expected_exit_code":"0"}, verbose=False)
        # instance.execute(["chgrp", "-R", arg["new_group"], arg["fileorfolder_path"]])
        result = execute_command(instance, {"command":["stat", "-c", "%G", arg["fileorfolder_path"]], "expected_exit_code":"0"}, verbose=False)
        # result = instance.execute(["stat", "-c", "%G", arg["fileorfolder_path"]])
        if arg["new_group"] in result.stdout:
            if verbose:
                print(Fore.GREEN + "      Group "+arg["new_group"]+" has been added to "+arg["fileorfolder_path"]+"!" + Style.RESET_ALL)
            return 0
        print(Fore.RED + "      Error group "+arg["new_group"]+" was not added to "+arg["fileorfolder_path"]+"..." + Style.RESET_ALL)
        return 1
    if verbose:
        print(Fore.YELLOW +"      "+ arg["fileorfolder_path"] +" is already in group "+ arg["new_group"] +Style.RESET_ALL)
    return 0

def change_permission(instance, arg, verbose=True):
    result = instance.execute(["chmod", "-R", arg["owner"]+arg["group"]+arg["other"], arg["file_path"]])
    if result.exit_code == 0:
        if verbose:
            print(Fore.GREEN+"      "+"Permission "+arg["owner"]+arg["group"]+arg["other"]+" added to "+arg["file_path"]+Style.RESET_ALL)
        return 0
    print(Fore.RED+"      New permissions failed to "+arg["file_path"]+Style.RESET_ALL)

def create_local_group(instance, arg, verbose=True):
    """ Create a local group on the remote instance """
    result = execute_command(instance, {"command":["cat", "/etc/group"], "expected_exit_code":"0"}, verbose=False)
    # result = instance.execute(["cat", "/etc/group"])
    if arg["new_group"] in result.stdout:
        if verbose:
            print(Fore.YELLOW+"      "+arg["new_group"]+" group has already created" +Style.RESET_ALL)
        return 0
    execute_command(instance, {"command":["groupadd", arg["new_group"]], "expected_exit_code":"0"}, verbose=False)
    # instance.execute(["groupadd", arg["new_group"]])
    result = execute_command(instance, {"command":["cat", "/etc/group"], "expected_exit_code":"0"}, verbose=False)
    # result = instance.execute(["cat", "/etc/group"])
    if arg["new_group"] in result.stdout:
        if verbose:
            print(Fore.GREEN+"      "+arg["new_group"]+ " group was created" +Style.RESET_ALL)
        return 0
    print(Fore.RED+ "      Error during "+arg["new_group"]+" group creation..." +Style.RESET_ALL)
    return 1

def upgrade(instance, verbose=True):
    """ Update the linux kernel on the remote instance """
    result = instance.execute(["apt-get", "-y", "upgrade"])
    if result.exit_code == 0:
        if verbose:
            print(Fore.GREEN+"      Upgrade!"+Style.RESET_ALL)
        return 0
    print(Fore.RED+"      Upgrade failed"+Style.RESET_ALL)
    return 1

# In progress...
def add_apt_repository(instance, arg, verbose=True):
    """ Add new referential on the remote instance """
    result = instance.execute(["add-apt-repository", arg["ppa_repository"]])
    if verbose:
        print("      Add repository "+str(result.exit_code))
    return 0

def restart_service(instance, arg, verbose=True):
    """ Restart the service specified in arg on the remote instance """
    execute_command(instance, {"command":["systemctl", "restart", arg["service"]], "expected_exit_code":"0"}, verbose=False)
    result = execute_command(instance, {"command":["systemctl", "status", arg["service"]], "expected_exit_code":"0"}, verbose=False)
    if "Active: active" in result.stdout:
        if verbose:
            print(Fore.GREEN+ "      "+arg["service"]+" is running!"+Style.RESET_ALL)
        return 0
    print(Fore.RED+ "      "+arg["service"]+" is not running!"+Style.RESET_ALL)
    return 1

def add_nameserver(instance, arg, verbose=True):
    """ Add new dns's ip on the file /etc/resolv.conf on the remote instance """
    resolveconf = open("simulation/workstations/"+instance.name+"/tmp-resolved.conf", "a+")
    resolveconf.write("nameserver "+arg["nameserver_ip"]+"\n")
    resolveconf.close()
    time.sleep(1)
    upload_file(instance, {"instance_path":"/etc/resolv.conf", "host_manager_path":"simulation/workstations/"+instance.name+"/tmp-resolved.conf"}, verbose=False)
    execute_command(instance, {"command":["chmod", "777", "/etc/resolv.conf"], "expected_exit_code":"0"}, verbose=False)
    # instance.execute(["chmod", "777", "/etc/resolv.conf"])

    result = execute_command(instance, {"command":["cat", "/etc/resolv.conf"], "expected_exit_code":"0"}, verbose=False)
    # result = instance.execute(["cat", "/etc/resolv.conf"]).stdout
    if arg["nameserver_ip"] in result.stdout:
        if verbose:
            print(Fore.GREEN +"      "+ arg["nameserver_ip"]+" has been added to nameserver list!" + Style.RESET_ALL)
        return 0
    print(Fore.RED + "      Error durind adding nameserver" + Style.RESET_ALL)
    return 1

def clear_nameserver(instance, verbose=True):
    """ Delete content of the file /etc/resolv.conf on the remote instance """
    try:
        if instance.files.delete_available():
            instance.files.delete("/etc/resolv.conf")
        try:
            os.remove("simulation/workstations/"+instance.name+"/tmp-resolved.conf")
        except:
            pass
        resolveconf = open("simulation/workstations/"+instance.name+"/tmp-resolved.conf", "a+")
        resolveconf.close()
        upload_file(instance, {"instance_path":"/etc/resolv.conf", "host_manager_path":"simulation/workstations/"+instance.name+"/tmp-resolved.conf"}, verbose=False)
        if verbose:
            print(Fore.GREEN + "      Resolv.conf file is clear!" + Style.RESET_ALL)
        return 0
    except:
        print(Fore.RED + "      Resolv.conf file can't be clear" + Style.RESET_ALL)
        return 1

def push_sim_user(instance, verbose=True):
    """ Push life script to the remote instance and make some
    installation and configuration to execute it """
    users_dict = {}
    users_list = []

    if create_local_group(instance, {"new_group":"simulation"}, verbose=False) == 1:
        return 1
    execute_command(instance, {"command":["mkdir", "/tmp/Documents/"], "expected_exit_code":"0"}, verbose=False)
    if change_fileorfolder_group_owner(instance, {"fileorfolder_path":"/tmp/Documents/", "new_group":"simulation"}, verbose=False) == 1:
        return 1
    instance.execute(["chmod", "770", "-R", "/tmp/Documents/"])
    execute_command(instance, {"command":["chmod", "777", "-R", "/tmp/Documents/"], "expected_exit_code":"0"}, verbose=False)
    conf_tmp = load_json_file("simulation/Configurations/conf_sim.json")
    for workstation in conf_tmp["workstations"]:
        if workstation["hostname"] == instance.name:
            for user in workstation["users"]:
                users_list.append(user)
                if add_user2group(instance, {"username":user["name"], "group_name":"simulation"}, verbose=False) == 1:
                    return 1

    users_dict["users"] = users_list
    dump_json_file(users_dict, "simulation/workstations/"+instance.name+"/users.json")

    if install(instance, {"module":"firefox"}, verbose=False) == 1:
        return 1
    if install_python_packages(instance, {"package":"beautifulsoup4"}, verbose=False) == 1:
        return 1
    if install_python_packages(instance, {"package":"pysmb"}, verbose=False) == 1:
        return 1
    if install_python_packages(instance, {"package":"selenium"}, verbose=False) == 1:
        return 1
    if install_python_packages(instance, {"package":"essential-generators"}, verbose=False) == 1:
        return 1
    if install_python_packages(instance, {"package":"colorama"}, verbose=False) == 1:
        return 1
    
    instance.files.recursive_put("sim_user", "/tmp/sim_user")
    if upload_file(instance, {"instance_path":"/tmp/sim_user/users.json", "host_manager_path":"simulation/workstations/"+instance.name+"/users.json"}, verbose=False) == 1:
        return 1
    if change_fileorfolder_group_owner(instance, {"new_group":"simulation", "fileorfolder_path":"/tmp/sim_user"}, verbose=False) == 1:
        return 1
    instance.execute(["chmod", "-R", "g+rwx", "/tmp/sim_user"])
    if verbose:
        print(Fore.GREEN + "      User's script have been push and are ready to be launch!" + Style.RESET_ALL)
    return 0

# In progress...
def configure_iptables(instance, verbose=True):
    """ In proress """
    if install(instance, {"module":"ulogd2"}, verbose=False) == 1:
        return 1
    instance.execute(["iptables", "-A", "INPUT", "-i", "eth1", "-p", "tcp", "-m", "state", "--state", "NEW", "-j", "NFLOG", "--nflog-prefix", "[iptables]"])
    instance.execute(["iptables", "-A", "OUTPUT", "-o", "eth1", "-p", "tcp", "-m", "state", "--state", "NEW", "-j", "NFLOG", "--nflog-prefix", "[iptables]"])
    instance.execute(["iptables", "-A", "INPUT", "-i", "eth1", "-p", "tcp", "-m", "state", "--state", "NEW", "-j", "NFLOG", "--nflog-prefix", "[iptables]"])
    instance.execute(["iptables", "-A", "OUTPUT", "-o", "eth1", "-p", "tcp", "-m", "state", "--state", "NEW", "-j", "NFLOG", "--nflog-prefix", "[iptables]"])
    if verbose:
        print(Fore.GREEN + "      Iptables logs have been configured to be generated!" + Style.RESET_ALL)
    return 0

# In progress...
def flush_iptables(instance, verbose=True):
    """ In progress """
    instance(["iptables", "-F"])
    return 0

def git_clone(instance, arg, verbose=True):
    nameserver_ips = save_nameserver_ip(instance)
    clear_nameserver(instance, verbose=False)
    add_nameserver(instance, {"nameserver_ip":"8.8.8.8"}, verbose=False)
    if arg["branch"] == "":
        execute_command(instance, {"command":["git", "clone", arg["repository"], arg["instance_path"]], "expected_exit_code":"0"}, verbose=False)
    else:
        execute_command(instance, {"command":["git", "clone", "--branch", arg["branch"], arg["repository"], arg["instance_path"]], "expected_exit_code":"0"}, verbose=False)
    clear_nameserver(instance, verbose=False)
    for nameserver_ip in nameserver_ips:
        add_nameserver(instance, {"nameserver_ip":nameserver_ip}, verbose=False)
################
# CERTIFICATES #
################
###### CA certificate
def generate_root_ca(instance, arg, verbose=True):
    """Generate CA certificate and upload it on the remote instance"""
    os.makedirs("simulation/workstations/"+instance.name+"/ca/"+arg["private_key_ca_certificate_name"], exist_ok=True)

    ###### Generate key
    ca_key = crypto.PKey()
    ca_key.generate_key(crypto.TYPE_RSA, int(arg["bits"]))

    ###### Generate certificate
    ca_cert = crypto.X509()
    ca_cert.set_version(int(arg["version"]))
    if arg["serial"] != "":
        ca_cert.set_serial_number(random.randint(50000000, 100000000))
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
        crypto.X509Extension(b"subjectKeyIdentifier", False, b"hash", subject=ca_cert)
    ])
    ca_cert.add_extensions([
        crypto.X509Extension(b"basicConstraints", False, b"CA:TRUE"),
        crypto.X509Extension(b"keyUsage", False, b"keyCertSign,cRLSign")
    ])

    ca_cert.sign(ca_key, "sha256")

    ###### Dump certificate
    with open("simulation/workstations/"+instance.name+"/ca/"+arg["private_key_ca_certificate_name"]+"/"+arg["private_key_ca_certificate_name"]+".cert", "wt") as certificate:
        certificate.write(crypto.dump_certificate(crypto.FILETYPE_PEM, ca_cert).decode("utf-8"))

    ###### Dump key
    with open("simulation/workstations/"+instance.name+"/ca/"+arg["private_key_ca_certificate_name"]+"/"+arg["private_key_ca_certificate_name"]+".key", "wt") as private_key:
        private_key.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, ca_key).decode("utf-8"))

    ###### Create directory
    instance.execute(["mkdir", "/ca"])
    instance.execute(["mkdir", "/ca/"+arg["private_key_ca_certificate_name"]])

    if upload_file(instance, {"instance_path":"/ca/"+arg["private_key_ca_certificate_name"]+"/"+arg["private_key_ca_certificate_name"]+".key", "host_manager_path": "simulation/workstations/"+instance.name+"/ca/"+arg["private_key_ca_certificate_name"]+"/"+arg["private_key_ca_certificate_name"]+".key"}, verbose=False) == 1:
        return 1
    if upload_file(instance, {"instance_path":"/ca/"+arg["private_key_ca_certificate_name"]+"/"+arg["private_key_ca_certificate_name"]+".cert", "host_manager_path": "simulation/workstations/"+instance.name+"/ca/"+arg["private_key_ca_certificate_name"]+"/"+arg["private_key_ca_certificate_name"]+".cert"}, verbose=False) == 1:
        return 1
    if verbose:
        print(Fore.GREEN + "      CA: ["+arg["private_key_ca_certificate_name"]+"] have been generated!" + Style.RESET_ALL)
    return 0
###### Middle certificate
def generate_middle_certificates(instance, arg, verbose=True):
    """Generate middle certificate and upload it on the remote instance"""
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
        middle_cert.set_serial_number(random.randint(50000000, 100000000))
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
        crypto.X509Extension(b"subjectKeyIdentifier", False, b"hash", subject=middle_cert)
    ])
    middle_cert.add_extensions([
        crypto.X509Extension(b"authorityKeyIdentifier", False, b"keyid:always", issuer=ca_cert),
        crypto.X509Extension(b"basicConstraints", False, b"CA:TRUE"),
        crypto.X509Extension(b"keyUsage", False, b"keyCertSign, cRLSign")
    ])

    middle_cert.set_pubkey(middle_key)
    middle_cert.sign(ca_key, "sha256")

    # Verify certificate chain
    store = crypto.X509Store()
    store.add_cert(ca_cert)
    ctx = crypto.X509StoreContext(store, middle_cert)
    if ctx.verify_certificate() == None:
        if verbose:
            print(Fore.GREEN + "      Certificate chain is working!" + Style.RESET_ALL)
        else:
            print(Fore.RED + "      Failed during certificate generation..." + Style.RESET_ALL)

    # Dump middle certificate
    with open("simulation/workstations/"+instance.name+"/middle_cert/"+arg["private_key_middle_certificate_name"]+"/"+arg["private_key_middle_certificate_name"]+".cert", "wt") as certificate:
        certificate.write(crypto.dump_certificate(crypto.FILETYPE_PEM, middle_cert).decode("utf-8"))

    # Dump middle key
    with open("simulation/workstations/"+instance.name+"/middle_cert/"+arg["private_key_middle_certificate_name"]+"/"+arg["private_key_middle_certificate_name"]+".key", "wt") as private_key:
        private_key.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, middle_key).decode("utf-8"))

    ###### Create directory
    instance.execute(["mkdir", "/middle_cert"])
    instance.execute(["mkdir", "/middle_cert/"+arg["private_key_middle_certificate_name"]])
    instance.execute(["mkdir", "/middle_cert/"+arg["private_key_middle_certificate_name"]+"/"])

    if upload_file(instance, {"instance_path":"/middle_cert/"+arg["private_key_middle_certificate_name"]+"/"+arg["private_key_middle_certificate_name"]+".key", "host_manager_path": "simulation/workstations/"+instance.name+"/middle_cert/"+arg["private_key_middle_certificate_name"]+"/"+arg["private_key_middle_certificate_name"]+".key"}, verbose=False) == 1:
        return 1
    if upload_file(instance, {"instance_path":"/middle_cert/"+arg["private_key_middle_certificate_name"]+"/"+arg["private_key_middle_certificate_name"]+".cert", "host_manager_path": "simulation/workstations/"+instance.name+"/middle_cert/"+arg["private_key_middle_certificate_name"]+"/"+arg["private_key_middle_certificate_name"]+".cert"}, verbose=False) == 1:
        return 1
    if upload_file(instance, {"instance_path":"/middle_cert/"+arg["private_key_middle_certificate_name"]+"/"+arg["ca_name"]+".cert", "host_manager_path": "simulation/workstations/"+arg["ca_holder"]+"/ca/"+arg["ca_name"]+"/"+arg["ca_name"]+".cert"}, verbose=False) == 1:
        return 1
    if verbose:
        print(Fore.GREEN + "      Middle cert: ["+arg["private_key_middle_certificate_name"]+"] have been generated!" + Style.RESET_ALL)
    return 0
###### Certificate
def generate_certificates(instance, arg, verbose=True):
    """Generate certificate and upload it on the remote instance"""
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
        client_cert.set_serial_number(random.randint(50000000, 100000000))
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
        crypto.X509Extension(b"subjectKeyIdentifier", False, b"hash", subject=client_cert)
    ])
    client_cert.add_extensions([
        crypto.X509Extension(b"authorityKeyIdentifier", False, b"keyid:always", issuer=middle_cert),
        crypto.X509Extension(b"subjectAltName", False, b"DNS:"+arg["dns"].encode("utf-8"))
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
            print(Fore.GREEN + "      Certificate chain is working!" + Style.RESET_ALL)
    else:
        print(Fore.RED + "      Failed during certificate generation..." + Style.RESET_ALL)

    # Dump certificate
    with open("simulation/workstations/"+instance.name+"/cert/"+arg["private_key_certificate_name"]+"/"+arg["private_key_certificate_name"]+".cert", "wt") as certificate:
        certificate.write(crypto.dump_certificate(crypto.FILETYPE_PEM, client_cert).decode("utf-8"))

    # Dump key
    with open("simulation/workstations/"+instance.name+"/cert/"+arg["private_key_certificate_name"]+"/"+arg["private_key_certificate_name"]+".key", "wt") as private_key:
        private_key.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, client_key).decode("utf-8"))

    ###### Create directory
    instance.execute(["mkdir", "/certs"])
    instance.execute(["mkdir", "/certs/"+arg["private_key_certificate_name"]])
    if upload_file(instance, {"instance_path":"/certs/"+arg["private_key_certificate_name"]+"/"+arg["private_key_certificate_name"]+".key", "host_manager_path": "simulation/workstations/"+instance.name+"/cert/"+arg["private_key_certificate_name"]+"/"+arg["private_key_certificate_name"]+".key"}, verbose=False) == 1:
        return 1
    if upload_file(instance, {"instance_path":"/certs/"+arg["private_key_certificate_name"]+"/"+arg["private_key_certificate_name"]+".cert", "host_manager_path": "simulation/workstations/"+instance.name+"/cert/"+arg["private_key_certificate_name"]+"/"+arg["private_key_certificate_name"]+".cert"}, verbose=False) == 1:
        return 1
    if upload_file(instance, {"instance_path":"/certs/"+arg["private_key_certificate_name"]+"/"+arg["middle_name"]+".cert", "host_manager_path": "simulation/workstations/"+arg["middle_holder"]+"/middle_cert/"+arg["middle_name"]+"/"+arg["middle_name"]+".cert"}, verbose=False) == 1:
        return 1
    if upload_file(instance, {"instance_path":"/certs/"+arg["private_key_certificate_name"]+"/"+arg["ca_name"]+".cert", "host_manager_path": "simulation/workstations/"+arg["ca_holder"]+"/ca/"+arg["ca_name"]+"/"+arg["ca_name"]+".cert"}, verbose=False) == 1:
        return 1
    if verbose:
        print(Fore.GREEN + "      Cert: ["+arg["private_key_certificate_name"]+"] have been generated!" + Style.RESET_ALL)

    return 0
### Diffie-Hellman
def generate_dh_key(instance, arg, verbose=True):
    """Generate diffie-hellman and upload it on the remote instance"""
    subprocess.run(["openssl", "dhparam", "-out", "simulation/workstations/"+instance.name+"/"+arg["dh_name"]+"-"+arg["key_size"]+".key", arg["key_size"]], check=True, capture_output=True)
    
    ###### Create directory
    instance.execute(["mkdir", "/certs"])
    instance.execute(["mkdir", "/certs/dh/"])
    if upload_file(instance, {"instance_path":"/certs/dh/"+arg["dh_name"]+"-"+arg["key_size"]+".key", "host_manager_path": "simulation/workstations/"+instance.name+"/"+arg["dh_name"]+"-"+arg["key_size"]+".key"}, verbose=False) == 1:
        return 1
    if verbose:
        print(Fore.GREEN + "      Diffie-Hellman key have been generated!" + Style.RESET_ALL)
    return 0

##########################
# Devices configurations #
##########################
def install_virtual_camera(instance, arg, verbose=True):
    install(instance, {"module":"wget"}, verbose=False)
    install(instance, {"module":"v4l2loopback-dkms"}, verbose=False)
    install(instance, {"module":"ffmpeg"}, verbose=False)

    result = instance.execute(["modprobe", "v4l2loopback"])
    if result.exit_code == 1:
        module_path = result.stderr.split(" ")[-1]
    result = instance.execute(["ls", "/lib/modules"])
    execute_command(instance, {"command":["cp", "-R", "/lib/modules/"+result.stdout.split("\n")[0], module_path[:-1]], "expected_exit_code":"0"}, verbose=False)

    nameserver_ips = save_nameserver_ip(instance)
    clear_nameserver(instance, verbose=False)
    add_nameserver(instance, {"nameserver_ip":"8.8.8.8"}, verbose=False)
    execute_command(instance, {"command":["wget", "-O", "/root/test.mp4", arg["video_url"]], "expected_exit_code":"0"}, verbose=False)
    clear_nameserver(instance, verbose=False)
    for nameserver_ip in nameserver_ips:
        add_nameserver(instance, {"nameserver_ip":nameserver_ip}, verbose=False)

    remote_file = open("simulation/workstations/"+instance.name+"/video_emulation.sh", "w")
    remote_file.write("#!/bin/bash\n")
    remote_file.write("ffmpeg -re -stream_loop -1 -i /root/test.mp4 -f v4l2 /dev/video* \n")
    remote_file.close()
    if upload_file(instance, {"instance_path":"/root/video_emulation.sh", "host_manager_path":"simulation/workstations/"+instance.name+"/video_emulation.sh"}, verbose=False):
        return 1  
    change_permission(instance, {"file_path":"/root/video_emulation.sh", "owner":"7", "group":"5", "other":"5"}, verbose=False)

    execute_command(instance, {"command":["modprobe", "v4l2loopback"], "expected_exit_code":"0"}, verbose=False)
    execute_command(instance, {"command":["start-stop-daemon", "--background", "--name", "dummy_video", "--start", "--quiet", "--chuid", "root", "--exec", "/root/video_emulation.sh"], "expected_exit_code":"0"}, verbose=False)

# {"name":"enable_ssl", "args": {"cert_path":"/certs/videoCenter.silicom.com/videoCenter.silicom.com.cert","key_path":"/certs/videoCenter.silicom.com/videoCenter.silicom.com.key","ca_dir":"/certs/videoCenter.silicom.com/","cas_path":["/certs/videoCenter.silicom.com/caroot.com.cert","/certs/videoCenter.silicom.com/silicom.com.cert"]} }
#"username":"camera1", "password":"camera123", "private_key_certificate_name":"camera1.silicom.com"