import OpenSSL.crypto as crypto
from .logic_actions_utils import install, upload_file, restart_service, generate_root_ca, generate_middle_certificates, generate_certificates, generate_dh_key

def install_openvpn(instance, arg, verbose=True):
    """  """
    install(instance, {"module":"openvpn"}, verbose=True)
    generate_dh_key(instance, {"dh_name":"openvpn", "key_size":"2048"})
    
    server_conf = open("simulation/workstations/"+instance.name+"/server_openvpn.conf", "w")
    server_conf.write("port 1197\n")
    server_conf.write("proto udp\n")
    server_conf.write("dev tun\n")
    server_conf.write("ca /certs/"+arg["private_key_certificate_name"]+"/"+arg["private_key_middle_certificate_name"]+".cert\n")
    server_conf.write("cert /certs/"+arg["private_key_certificate_name"]+"/"+arg["private_key_certificate_name"]+".cert\n")
    server_conf.write("key /certs/"+arg["private_key_certificate_name"]+"/"+arg["private_key_certificate_name"]+".key\n")
    server_conf.write("dh /certs/dh/openvpn-2048.key\n")
    server_conf.write("server 10.122.0.0 255.255.255.0 \n")
    server_conf.write("push \"10.122.1.0 255.255.255.0\"\n")
    server_conf.write("keepalive \n")
    server_conf.write("cipher AES-128-CBC \n")
    server_conf.write("comp-lzo \n")
    server_conf.write("max-clients "+arg["max_client"]+"\n")
    if arg["user"] == "":
        server_conf.write("user nobody\n")
    else:
        server_conf.write("user "+arg["user"]+"\n")
    if arg["group"] == "":
        server_conf.write("group nobody\n")
    else:
        server_conf.write("group "+arg["group"]+"\n")
    server_conf.write("persist-key\n")
    server_conf.write("persist-tun\n")
    server_conf.write("status openvpn-status.log\n")
    server_conf.write("log openvpn.log\n")
    server_conf.write("verb 9\n")
    server_conf.close()
    if upload_file(instance, {"instance_path":"/etc/openvpn/server.conf", "host_manager_path": "simulation/workstations/"+instance.name+"/server_openvpn.conf"}, verbose=False) == 1:
        return 1
    if restart_service(instance, {"service":"openvpn"}) == 1:
        return 1



#{"name":"generate_root_ca", "args": {"private_key_ca_certificate_name":"caroot.com","bits":"2048","version":"2","serial":"","C":"FR","ST":"France","L":"Paris","O":"carootemission","CN":"caroot.com","days_validity":"360"} },