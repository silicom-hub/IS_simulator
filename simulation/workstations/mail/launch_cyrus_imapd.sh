#!/bin/bash
debconf-set-selections <<< "postfix postfix/mailname string mail.boulangerie.local" 
debconf-set-selections <<< "postfix postfix/main_mailer_type string 'Internet Site'" 
DEBIAN_FRONTEND=noninteractive apt-get install -y cyrus-imapd 
touch /var/lib/cyrus/tls_sessions.db 
chown cyrus:mail /var/lib/cyrus/tls_sessions.db 
sed -i -e 's|#admins: cyrus|admins: cyrus|' /etc/imapd.conf 
sed -i -e 's|sasl_pwcheck_method: auxprop|sasl_pwcheck_method: saslauthd|' /etc/imapd.conf 
sed -i -e 's|#sasl_mech_list: PLAIN|sasl_mech_list: PLAIN|' /etc/imapd.conf 

sed -i -e 's|pop3|#pop3|' /etc/cyrus.conf 
sed -i -e 's|nntp|#nntp|' /etc/cyrus.conf 
sed -i -e 's|http|#http|' /etc/cyrus.conf 
systemctl restart cyrus-imapd 
sleep 2 
cyradm -u cyrus -w cyrus123 localhost << sample
cm user.aquemat
cm user.tgourmelen
sample
