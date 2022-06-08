""" This file contains who configures samba server """
from colorama import Fore, Style
from .logic_actions_utils import create_execute_command_remote_bash, execute_command, install, upload_file, delete_file, create_local_user, restart_service, create_local_group, change_fileorfolder_group_owner, add_user2group

def install_samba(instance, verbose=True):
    """ Install and configure samba on the remote instance.
    args {
         }
    Returns:
        int: Return 1 if the function works successfully, otherwise 0.
    """
    if install(instance, {"module":"samba"}, verbose=False) == 1:
        return 1
    execute_command(instance, {"command":["cp", "/etc/samba/smb.conf", "/etc/samba/smb.conf.origin"], "expected_exit_code":"0"}, verbose=False)
    if delete_file(instance, {"instance_path":"/etc/samba/smb.conf"}, verbose=False) == 1:
        return 1
    file_samba_conf = open("simulation/workstations/"+instance.name+"/smb.conf", "a+")
    file_samba_conf.write("[global] \n")
    file_samba_conf.write("     workgroup = WORKGROUP\n")
    file_samba_conf.write("     log file = /var/log/samba/samba.log\n")
    file_samba_conf.write("     log level = 2\n")
    file_samba_conf.close()
    if upload_file(instance, {"instance_path":"/etc/samba/smb.conf", "host_manager_path":"simulation/workstations/"+instance.name+"/smb.conf"}, verbose=False) == 1:
        return 1
    if verbose:
        print(Fore.GREEN+"      Samba have been installed and configured successfully!"+Style.RESET_ALL)
    return 0

def add_share_file(instance, args, verbose=True):
    """" Add new share folder configure with restricted acces on remote folder 
    arg (dict of str: Optional): This argument list maps arguments and their value.
            {
                share_file_name (str): This value is the share file name.
                comment (str): This value is a comment about the share file service.
                private (str): This value is a boolean who define if the samba service is private or public.
                browseable (str): This is a boolean who indicate if client could see share file.
                    Examples:
                    users -> yes
                    users -> no
                writable (str): This is a boolean who indicate if client could modified objects in share file.
                    Examples: 
                    writable -> yes
                    writable -> no
                valid_users (list): This value is a user list who can access to the share file.
                users (list): This value is a user list with their surname and password.
                    Examples:
                    users -> [["ceo","ceo123"], ... ,["intern","intern123"]]
            }
    """
    execute_command(instance, {"command":["mkdir", "-p", "/srv/samba/"+args["share_file_name"]+"/"], "expected_exit_code":"0"}, verbose=False)
    execute_command(instance, {"command":["touch", "/srv/samba/"+args["share_file_name"]+"/test.txt"], "expected_exit_code":"0"}, verbose=False)

    if create_local_group(instance, {"new_group":args["share_file_name"]}, verbose=False) == 1:
        return 1
    if change_fileorfolder_group_owner(instance, {"fileorfolder_path":"/srv/samba/"+args["share_file_name"]+"/", "new_group":args["share_file_name"]}, verbose=False) == 1:
        return 1
    execute_command(instance, {"command":["chmod", "-R", "670", "/srv/samba/"+args["share_file_name"]+"/"], "expected_exit_code":"0"}, verbose=False)

    if args["private"] == "true":
        for user in args["users"]:
            if create_local_user(instance, {"username":user[0], "password":user[1]}, verbose=False) == 1:
                return 1
            
            create_execute_command_remote_bash(instance, {"script_name":"user_smb_"+user[0]+".sh", "commands":[
                                                                                                               "echo -e \""+user[1]+"\n"+user[1]+"\" | smbpasswd -a "+user[0]
                                                                                                              ], "delete":"false"}, verbose=False)
        
            
            if add_user2group(instance, {"group_name":args["share_file_name"], "username":user[0]}, verbose=False) == 1:
                return 1

    file_samba_conf = open("simulation/workstations/"+instance.name+"/smb.conf", "a+")
    file_samba_conf.write("["+args["share_file_name"]+"] \n")
    file_samba_conf.write("     comment = "+args["comment"]+"\n")
    file_samba_conf.write("     path = /srv/samba/"+args["share_file_name"]+"/\n")
    file_samba_conf.write("     browseable = "+args["browseable"]+"\n")
    if args["private"] == "true":
        file_samba_conf.write("     guest ok = yes\n")
        file_samba_conf.write("     valid users = ")
        for valid_users in args["valid_users"]:
            file_samba_conf.write(valid_users+",")
        file_samba_conf.write("\n")
    else:
        file_samba_conf.write("guest ok = no\n")
    file_samba_conf.write("     writable = "+args["writable"]+"\n")
    file_samba_conf.close()
    if upload_file(instance, {"instance_path":"/etc/samba/smb.conf", "host_manager_path":"simulation/workstations/"+instance.name+"/smb.conf"}, verbose=False):
        return 1
    if restart_service(instance, {"service":"smbd"}, verbose=False) == 1:
        return 1
    if verbose:
        print(Fore.GREEN+"      Sharefile ["+args["share_file_name"]+"] have been added successfully!"+Style.RESET_ALL)
    return 0

# {"name":"install_samba", "args": {"":""} },
# {"name":"add_shareFile", "args": {"share_file_name":"shareFile","comment":"Fichier partage silicom!",
#                                     "private":"true","browseable":"yes","writable":"yes","valid_users":["user","hacker"],
#                                     "users":[["hacker","hacker123"],["user","user123"]]} }

# {"name":"smb_cycle","rep":"1","begin":"0","args":{"nb_actions":"10","username":"aquemat","password":"aquemat123","workstation_name":"workstation1","server_name":"samba.silicom.com","server_ip":"10.122.1.17","service_name":"shareFile"}}
