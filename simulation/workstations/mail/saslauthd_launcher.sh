#!/bin/bash 
systemctl restart saslauthd 
sed -i -e  s#OPTIONS='-c -m /var/run/saslauthd'#OPTIONS='-c -m /var/spool/postfix/var/run/saslauthd'# /etc/default/saslauthd 
chmod 1777 /etc/resolv.conf 
chmod 1777 -R /var/spool/postfix/ 
systemctl restart saslauthd 
