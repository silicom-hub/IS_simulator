from colorama import Fore, Style
from .logic_actions_utils import upload_file, change_fileorfolder_user_owner, restart_service

def rsyslog_client(client, instance, arg, verbose=True):
    facility = 1
    instance.execute(["sed","-i","/imklog/s/^/#/","/etc/rsyslog.conf"])
    for log in arg["log_files"]:
        file_conf = open("simulation/workstations/"+instance.name+"/"+log+".conf","w")
        if log == "authentication":
            file_conf.write("auth,authpriv.* @"+arg["ip_log_server"]+":5001\n")
        if log == "mail":
            file_conf.write("mail.* @"+arg["ip_log_server"]+":5001\n")
        if log == "apache2":
            file_conf.write("module(load=\"imfile\" PollingInterval=\"10\") \n")
            file_conf.write("input(type=\"imfile\" File=\"/var/log/apache2/access.log\" Tag=\"http_access\" Severity=\"info\" Facility=\"local"+str(facility)+"\") \n")
            file_conf.write("input(type=\"imfile\" File=\"/var/log/apache2/error.log\" Tag=\"http_error\" Severity=\"error\" Facility=\"local"+str(facility)+"\") \n")
            file_conf.write("local"+str(facility)+".* @"+arg["ip_log_server"]+":5001 \n")
        if log == "iptables":
            file_conf.write("module(load=\"imfile\" PollingInterval=\"10\") \n")
            file_conf.write("input(type=\"imfile\" File=\"/var/log/ulog/syslogemu.log\" Tag=\"iptables\" Severity=\"info\" Facility=\"local"+str(facility)+"\") \n")
            file_conf.write("local"+str(facility)+".* @"+arg["ip_log_server"]+":5001 \n")
        if log == "squid":
            file_conf.write("module(load=\"imfile\" PollingInterval=\"10\") \n")
            file_conf.write("input(type=\"imfile\" File=\"/var/log/squid/access.log\" Tag=\"http_access\" Severity=\"info\" Facility=\"local"+str(facility)+"\") \n")
            file_conf.write("input(type=\"imfile\" File=\"/var/log/squid/cache.log\" Tag=\"http_cache\" Severity=\"info\" Facility=\"local"+str(facility)+"\") \n")
            file_conf.write("local"+str(facility)+".* @"+arg["ip_log_server"]+":5001 \n")
        if log == "snort":
            file_conf.write("module(load=\"imfile\" PollingInterval=\"10\") \n")
            file_conf.write("input(type=\"imfile\" File=\"/var/log/snort/alert\" Tag=\"snort\" Severity=\"alert\" Facility=\"local"+str(facility)+"\") \n")
            file_conf.write("local"+str(facility)+".* @"+arg["ip_log_server"]+":5001 \n")
        if log == "suricata":
            file_conf.write("module(load=\"imfile\" PollingInterval=\"10\") \n")
            file_conf.write("input(type=\"imfile\" File=\"/var/log/suricata/fast.log\" Tag=\"suricata\" Severity=\"alert\" Facility=\"local"+str(facility)+"\") \n")
            file_conf.write("local"+str(facility)+".* @"+arg["ip_log_server"]+":5001 \n")
        if log == "ldap":
            file_conf.write("module(load=\"imfile\" PollingInterval=\"10\") \n")
            file_conf.write("input(type=\"imfile\" File=\"/var/log/slapd.log\" Tag=\"slapd\" Severity=\"info\" Facility=\"local"+str(facility)+"\") \n")
            file_conf.write("local"+str(facility)+".* @"+arg["ip_log_server"]+":5001 \n")
        if log == "samba":
            file_conf.write("module(load=\"imfile\" PollingInterval=\"10\") \n")
            file_conf.write("input(type=\"imfile\" File=\"/var/log/samba/samba.log\" Tag=\"samba\" Severity=\"info\" Facility=\"local"+str(facility)+"\") \n")
            file_conf.write("local"+str(facility)+".* @"+arg["ip_log_server"]+":5001 \n")

        
        file_conf.close()
        upload_file(client,instance,{"instance_path":"/etc/rsyslog.d/"+log+".conf","host_manager_path":"simulation/workstations/"+instance.name+"/"+log+".conf"}, verbose=False)

    change_fileorfolder_user_owner(client,instance,{"new_owner":"syslog","file_path":"/etc/rsyslog.d/"+log+".conf"}, verbose=False)
    # instance.execute(["chmod","-R","777","/etc/rsyslog.d"])
    restart_service(client,instance,{"service":"rsyslog"}, verbose=False)