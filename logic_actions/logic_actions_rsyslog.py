"""This file contain all functions about log configuration """
from colorama import Fore, Style
from .logic_actions_utils import execute_command, upload_file, change_fileorfolder_user_owner, restart_service

def rsyslog_client(instance, arg, verbose=True):
    """ Configure rsyslog client to send log to log server on the remote instance """
    facility = 1
    execute_command(instance, {"command":["sed", "-i", "/imklog/s/^/#/", "/etc/rsyslog.conf"], "expected_exit_code":"0"}, verbose=False)
    for log in arg["log_files"]:
        file_conf = open("simulation/workstations/"+instance.name+"/"+log+".conf", "w", encoding="utf-8")
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
        if log == "motion":
            file_conf.write("module(load=\"imfile\" PollingInterval=\"10\") \n")
            file_conf.write("input(type=\"imfile\" File=\"/var/log/motion/motion.log\" Tag=\"motion\" Severity=\"info\" Facility=\"local"+str(facility)+"\") \n")
            file_conf.write("local"+str(facility)+".* @"+arg["ip_log_server"]+":5001 \n")

        file_conf.close()
        if upload_file(instance, {"instance_path":"/etc/rsyslog.d/"+log+".conf", "host_manager_path":"simulation/workstations/"+instance.name+"/"+log+".conf"}, verbose=False) == 1:
            return 1
        if change_fileorfolder_user_owner(instance, {"new_owner":"syslog", "file_path":"/etc/rsyslog.d/"+log+".conf"}, verbose=False) == 1:
            return 1
    if restart_service(instance, {"service":"rsyslog"}, verbose=False) == 1:
        return 1
    if verbose:
        print(Fore.GREEN+"      Install and configure rsyslog client successfully!"+Style.RESET_ALL)
    return 0
