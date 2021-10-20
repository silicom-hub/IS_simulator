#!/bin/bash
debconf-set-selections <<< "postfix postfix/mailname string workstation1.boulangerie.local" 
debconf-set-selections <<< "postfix postfix/main_mailer_type string 'Internet Site'" 
DEBIAN_FRONTEND=noninteractive apt-get install -y postfix 
touch /var/lib/cyrus/tls_sessions.db 
chown cyrus:mail /var/lib/cyrus/tls_sessions.db 
