from colorama import Fore, Style
from logic_actions.logic_actions_utils import install, update ,upload_file, delete_file

def zeek_installation(client,instance,args, verbose=True):
    install(client,instance,{"module":"zeek"}, verbose=False)

def snort_installation(client,instance,args, verbose=True):
    install(client,instance,{"module":"oinkmaster"}, verbose=False)
    install(client,instance,{"module":"snort-rules-default"}, verbose=False)
    file_snort_install = open("simulation/workstations/"+instance.name+"/file_snort_install.sh", "w")
    file_snort_install.write("#!/bin/bash\n")
    file_snort_install.write("########### snort installation ##########\n")
    file_snort_install.write("echo \"url = http://rules.emergingthreats.net/open-nogpl/snort-2.8.4/emerging.rules.tar.gz\" >> /etc/oinkmaster.conf\n")
    file_snort_install.write("DEBIAN_FRONTEND=noninteractive apt-get install -y -q snort\n")
    file_snort_install.write("oinkmaster -o /etc/snort/rules\n")
    file_snort_install.write("########### snort.conf ##########\n")
    file_snort_install.write("sed -i -e  \"s|ipvar HOME_NET any|ipvar HOME_NET "+args["network"]+"|\" /etc/snort/snort.conf \n")
    # file_snort_install.write("sed -i -e  \"s|include $HOME_NET|#include $HOME_NET|\" /etc/snort/snort.conf \n")
    # for rule in args["rules"]:
    #     print(rule)
    #     file_snort_install.write("echo \"include /etc/snort/rules/"+rule+"\" >> /etc/snort/snort.conf \n")
    file_snort_install.close()
    upload_file(client,instance,{"instance_path":"/root/file_snort_install.sh","host_manager_path":"simulation/workstations/"+instance.name+"/file_snort_install.sh"}, verbose=False)
    instance.execute(["chmod","+x","/root/file_snort_install.sh"])
    instance.execute(["./file_snort_install.sh"])
    delete_file(client,instance,{"instance_path":"/root/file_snort_install.sh"}, verbose=False)

    tmp = open("simulation/workstations/"+instance.name+"/local.rules", "w")
    tmp.write("alert tcp $HOME_NET any -> $EXTERNAL_NET any (msg:\"TEST\"; sid:10000001; rev:1;)")
    tmp.close()
    upload_file(client,instance,{"instance_path":"/etc/snort/rules/local.rules","host_manager_path":"simulation/workstations/"+instance.name+"/local.rules"}, verbose=False)

    result = instance.execute(["snort","-D","-i","eth1","-K","ascii","-l","/var/log/snort/","-c","/etc/snort/snort.conf"])
    if "exiting (0)" in result.stdout:
        if verbose:
            print( Fore.GREEN + "      Snort deamon started !" + Style.RESET_ALL )
    else:
        print( Fore.RED + "      Snort deamon failed ..." + Style.RESET_ALL )

def suricata_installation(client,instance,args, verbose=True):
    result = instance.execute(["add-apt-repository", "ppa:oisf/suricata-stable"])
    update(client,instance,{"":""}, verbose=False)
    result = instance.execute(["apt-cache", "policy","suricata"])
    install(client,instance,{"module":"suricata"}, verbose=False)
    install(client,instance,{"module":"suricata-dbg"}, verbose=False)
    suricata_conf = open("simulation/workstations/"+instance.name+"/file_suricata_install.sh", "w")
    suricata_conf.write("#!/bin/bash\n")
    suricata_conf.write("sed -i -e s#/var/lib/suricata/rules#/etc/suricata/rules# /etc/suricata/suricata.yaml\n")
    suricata_conf.close()
    upload_file(client,instance,{"instance_path":"/root/file_suricata_install.sh","host_manager_path":"simulation/workstations/"+instance.name+"/file_suricata_install.sh"}, verbose=False)
    instance.execute(["chmod","+x","/root/file_suricata_install.sh"])  
    instance.execute(["./file_suricata_install.sh"])                                                                                                                                                                                                                                                                                                                                                                        
    instance.execute(["systemctl","stop","suricata"])
    instance.execute(["touch","/etc/suricata/rules/suricata.yaml"])
    # instance.execute(["iptables","-I","FORWARD","-j","NFQUEUE"])

    # print( instance.execute(["suricata","-c","/etc/suricata/suricta.yaml","-q","0"]) )

    # Rules
    # instance.execute(["wget","-O","/etc/suricata/rules/emerging-attack_response.rules","http://www.emergingthreats.net/rules/emerging-attack_response.rules"])
    # instance.execute(["wget","-O","/etc/suricata/rules/rules/emerging-scan.rules","http://www.emergingthreats.net/rules/emerging-scan.rules"])
    # instance.execute(["wget","-O","/etc/suricata/rules/emerging-exploit.rules","http://www.emergingthreats.net/rules/emerging-exploit.rules"])
    # instance.execute(["wget","-O","/etc/suricata/rules/emerging-current_events.rules","http://www.emergingthreats.net/rules/emerging-current_events.rules"])
    # instance.execute(["wget","-O","/etc/suricata/rules/rules/emerging-voip.rules/emerging-malware.rules","http://www.emergingthreats.net/rules/emerging-voip.rules"])
    # instance.execute(["wget","-O","/etc/suricata/rules/rules/emerging-malware.rules","http://www.emergingthreats.net/rules/emerging-malware.rules"])
    # instance.execute(["wget","-O","/etc/suricata/rules/rules/emerging-dos.rules","http://www.emergingthreats.net/rules/emerging-dos.rules"])
    # instance.execute(["wget","-O","/etc/suricata/rules/emerging-drop.rules","http://www.emergingthreats.net/rules/emerging-drop.rules"])
    # instance.execute(["wget","-O","/etc/suricata/rules/emerging-compromised.rules","http://www.emergingthreats.net/rules/emerging-compromised.rules"])
    # instance.execute(["wget","-O","/etc/suricata/rules/emerging-dshield.rules","http://www.emergingthreats.net/rules/emerging-dshield.rules"])
    # instance.execute(["wget","-O","/etc/suricata/rules/rules/emerging-botcc.rules","http://www.emergingthreats.net/rules/emerging-botcc.rules"])
    # instance.execute(["wget","-O","/etc/suricata/rules/rules/emerging-rbn.rules","http://www.emergingthreats.net/rules/emerging-rbn.rules"])
    # instance.execute(["wget","-O","/etc/suricata/rules/emerging-virus.rules","http://www.emergingthreats.net/rules/emerging-virus.rules"])
