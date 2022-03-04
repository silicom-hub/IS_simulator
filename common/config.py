from common.configuration_loader import *

from logic_actions import logic_actions_camera
from logic_actions import logic_actions_dns
from logic_actions import logic_actions_elk
from logic_actions import logic_actions_filebeat
from logic_actions import logic_actions_ldap
from logic_actions import logic_actions_mail
from logic_actions import logic_actions_proxy
from logic_actions import logic_actions_rsyslog
from logic_actions import logic_actions_samba
from logic_actions import logic_actions_security
from logic_actions import logic_actions_vpn
from logic_actions import logic_actions_web
from logic_actions import logic_actions_utils

import os

current_path = os.path.dirname(os.path.abspath(__file__))
# Software version
version_file = os.path.join(current_path, "..", "version.ini")
# Workstations functions
workstations_file = os.path.join(current_path, "workstations", "common.ini")

exclude_elements = ["Fore", "Style", "__builtins__", "__cached__", "__doc__", "__file__", "__loader__", "__name__",
                    "__package__", "__spec__", "Optional", "time", "os", "cv2", "time", "json", "random", "hashlib",
                    "subprocess", "crypto"]


class Config:

    @staticmethod
    def get_version():
        return parse_value(version_file, "SI_simulator", "version")

    @staticmethod
    def get_camera_methods():
        return [f for f in dir(logic_actions_camera) if f not in exclude_elements]

    @staticmethod
    def get_dns_methods():
        return [f for f in dir(logic_actions_dns) if f not in exclude_elements]

    @staticmethod
    def get_elk_methods():
        return [f for f in dir(logic_actions_elk) if f not in exclude_elements]

    @staticmethod
    def get_filebeat_methods():
        return [f for f in dir(logic_actions_filebeat) if f not in exclude_elements]

    @staticmethod
    def get_ldap_methods():
        return [f for f in dir(logic_actions_ldap) if f not in exclude_elements]

    @staticmethod
    def get_mail_methods():
        return [f for f in dir(logic_actions_mail) if f not in exclude_elements]

    @staticmethod
    def get_proxy_methods():
        return [f for f in dir(logic_actions_proxy) if f not in exclude_elements]

    @staticmethod
    def get_rsyslog_methods():
        return [f for f in dir(logic_actions_rsyslog) if f not in exclude_elements]

    @staticmethod
    def get_samba_methods():
        return [f for f in dir(logic_actions_samba) if f not in exclude_elements]

    @staticmethod
    def get_security_methods():
        return [f for f in dir(logic_actions_security) if f not in exclude_elements]

    @staticmethod
    def get_utils_methods():
        return [f for f in dir(logic_actions_utils) if f not in exclude_elements]

    @staticmethod
    def get_vpn_methods():
        return [f for f in dir(logic_actions_vpn) if f not in exclude_elements]

    @staticmethod
    def get_web_methods():
        return [f for f in dir(logic_actions_web) if f not in exclude_elements]

    @staticmethod
    def get_workstations_methods():
        return parse_values_list(workstations_file, "FUNCTIONS", "common")

    @staticmethod
    def get_available_workstations():
        return parse_values_list(workstations_file, "SIMULATION", "workstations")

    @staticmethod
    def get_authorized_values(arg):
        values = []
        if arg in authorized_args.keys():
            values = authorized_args[arg]
        return values


def compare_d_lists(first_list, second_list):
    # Arguments are lists of dictionaries
    for base in first_list:
        for compared in second_list:
            if base["name"] == compared["name"]:
                base.update(compared)
                continue
    return first_list


# Switch
workstation_methods = {
    "camera": Config.get_camera_methods,
    "dns": Config.get_dns_methods,
    "elk": Config.get_elk_methods,
    "filebeat": Config.get_filebeat_methods,  # TODO :add filebeat methods to common
    "ldap": Config.get_ldap_methods,
    "mail": Config.get_mail_methods,
    "proxy": Config.get_proxy_methods,
    "router": Config.get_workstations_methods,
    "rsyslog": Config.get_rsyslog_methods,
    "samba": Config.get_samba_methods,
    "security": Config.get_security_methods,
    "utils": Config.get_utils_methods,
    "vpn": Config.get_vpn_methods,
    "web": Config.get_web_methods,
    "workstation": Config.get_workstations_methods
}

authorized_args = {
    "install": ["module"],
    "execute_command": ["command", "execute_exit_code"],
    "add_nameserver": ["nameserver_ip"],

    "rsyslog_client": ["ip_log_server", "log_files"],
    "install_gnu_social_network": ["server_ip", "domain_name"],

    "download_file": [],

    "generate_root_ca": ["private_key_ca_certificate_name", "bits", "version", "serial", "C", "ST", "L", "O", "CN", "days_validity"],
    "generate_middle_certifications": ["ca_holder", "ca_name", "private_key_middle_certificate_name", "bits", "version", "serial", "C", "ST", "L", "O", "CN", "days_validity"],
    "generate_certificates": ["ca_holder", "ca_name", "middle_holder", "middle_name", "private_key_certificate_name", "bits", "version", "serial", "C", "ST", "L", "O", "CN", "days_validity", "dns"],
    "dns_installation": ["domain_name", "ip_resolution"],
    "dns_resolve_name": ["domain_name", "ip_resolution", "mail", "alias"],

    "ldap_create_domaine": ["root_password", "domaine_name", "domain", "organization", "ip_log_server"],
    "ldap_add_user": ["hostname", "username", "objectClass", "mail", "sn", "dn", "domain", "homeDirectory", "loginShell",
                      "password", "uidNumber", "gidNumber"],
    "ldap_client_config": ["ldap_ip", "base", "uri", "ldap_admin"],

    "mail_installation": ["ldap_ip", "ldap_domain", "ldap_dn", "ldap_manager", "ldap_manager_password", "ldap_port", "domain_name", "users_mailbox"],
    "enable_ssl": ["cert_path", "key_path", "ca_dir", "cas_path"],
    "enable_ssl_imapd": ["cert_path", "key_path", "ca_dir", "cas_path"],
    "enable_ssl_postfix": ["cert_path", "key_path", "ca_dir", "cas_path"],

    "create_local_user": ["username", "password"],
    "configure_iptables": ["share_file_name", "comment", "private", "browseable", "writable", "valid_users", "users"],
    "install_samba": [],
    "add_share_file": [],
    "install_virtual_camera": ["video_url", "remote_video_path_file"],
    "install_motion": ["motion_port", "security"],
    "install_zoneminder": [],

    "install_elk": ["logstash", "elasticsearch", "kibana", "fqdn_host", "ip_fqdn", "admin_name", "admin_passwd"],
    "push_sim_user": [],

}
