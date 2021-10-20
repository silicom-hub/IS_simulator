from colorama import Fore, Style
from .logic_actions_utils import install, upload_file, delete_file, create_local_user, restart_service, create_local_group, change_fileorfolder_group_owner, add_user2group

def install_samba(client,instance,args, verbose=True):
    install(client,instance,{"module":"samba"}, verbose=False)
    instance.execute(["cp","/etc/samba/smb.conf","/etc/samba/smb.conf.origin"])
    delete_file(client,instance,{"instance_path":"/etc/samba/smb.conf"}, verbose=False)
    file_samba_conf = open("simulation/workstations/"+instance.name+"/smb.conf","a+")
    file_samba_conf.write("[global] \n")
    file_samba_conf.write("     workgroup = WORKGROUP\n")
    file_samba_conf.write("     log file = /var/log/samba/samba.log\n")
    file_samba_conf.write("     log level = 5\n")
    file_samba_conf.close()
    upload_file(client,instance,{"instance_path":"/etc/samba/smb.conf","host_manager_path":"simulation/workstations/"+instance.name+"/smb.conf"}, verbose=False)

def add_shareFile(client,instance,args, verbose=True):
    instance.execute(["mkdir","-p","/srv/samba/"+args["share_file_name"]+"/"])
    create_local_group(client,instance,{"new_group":args["share_file_name"]}, verbose=False)
    change_fileorfolder_group_owner(client,instance,{"fileorfolder_path":"/srv/samba/"+args["share_file_name"]+"/","new_group":args["share_file_name"]}, verbose=False)
    instance.execute(["chmod","-R","670","/srv/samba/"+args["share_file_name"]+"/"])

    if args["private"] == "true":
        for user in args["users"]:
            create_local_user(client,instance,{"username":user[0],"password":user[1]}, verbose=False)
            add_user = open("simulation/workstations/"+instance.name+"/user_smb_"+user[0]+".sh","w")
            add_user.write("#!/bin/bash \n")
            add_user.write("echo -e \""+user[1]+"\n"+user[1]+"\" | smbpasswd -a "+user[0])
            add_user.close()
            upload_file(client,instance,{"instance_path":"/root/user_smb_"+user[0]+".sh","host_manager_path":"simulation/workstations/"+instance.name+"/user_smb_"+user[0]+".sh"}, verbose=False)
            instance.execute(["chmod","+x","/root/user_smb_"+user[0]+".sh"])
            instance.execute(["./user_smb_"+user[0]+".sh"])
            delete_file(client,instance,{"instance_path":"/root/user_smb_"+user[0]+".sh"}, verbose=False)
            add_user2group(client,instance,{"group_name":args["share_file_name"],"username":user[0]}, verbose=False)

    file_samba_conf = open("simulation/workstations/"+instance.name+"/smb.conf","a+")
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
    upload_file(client,instance,{"instance_path":"/etc/samba/smb.conf","host_manager_path":"simulation/workstations/"+instance.name+"/smb.conf"}, verbose=False)
    restart_service(client,instance,{"service":"smbd"}, verbose=False)

# {"name":"install_samba", "args": {"":""} },
# {"name":"add_shareFile", "args": {"share_file_name":"shareFile","comment":"Fichier partage silicom!",
#                                     "private":"true","browseable":"yes","writable":"yes","valid_users":["user","hacker"],
#                                     "users":[["hacker","hacker123"],["user","user123"]]} }
