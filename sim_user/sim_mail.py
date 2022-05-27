import time
import wget
import glob
import random
import tarfile
import subprocess
from colorama import Style, Fore
from essential_generators import DocumentGenerator
from mailLib import smtp_connect, imap_connect, send_mail, read_mailbox, download_attachements, delete_old_emails, delete_all_emails, read_mailbox_download_execute

def mail_cycle(args):
    """ Execute multiple mail actions [send_mail, read_mailbox_download_execute, download_attachements, delete_all_emails].
        args (dict of str): This argument list maps arguments and their value.
            {
                smtp_server_ip (str): This value is the smtp server's ip.
                imap_server_ip (str): This value is the imap server's ip.
                login (str): This value is the username login.
                password (str): This value is the password login.
                FROM (str): This value is the sender email address.
                TO (list): This value is a list of multiple recipient
                SUBJECT (str, Optional): This value is the email's subject content.
                MSG (str, Optional): This value is the email's message content.
                ATTACHEMENTS (list Optional):
            }
    
    Returns:
        None
    """
    smtp_server = args["smtp_server_ip"]
    imap_server = args["imap_server_ip"]
    imap_login = args["login"]
    imap_password = args["password"]
    FROM = args["FROM"]
    TO = args["TO"]
    SUBJECT = args["subject"]
    MSG = args["msg"]
    ATTACHEMENTS = args["attachements"]

    gen = DocumentGenerator()
    actions = ["send_mail","read_mailbox_download_execute","download_attachements","delete_all_emails"]
    for i in range(int(args["nb_actions"])):
        action = random.choices(actions, weights=[10,10,0,0])
        time.sleep(random.randint(30,60))
        if action == ["read_mailbox"]:
            read_mailbox(imap_server, imap_login, imap_password)
        elif action == ["download_attachements"]:
            download_attachements(imap_server, imap_login, imap_password)
        elif action == ["delete_all_emails"]:
            delete_all_emails(imap_server, imap_login, imap_password)
        elif action == ["send_mail"]:
            if len(TO) >= 1:
                to = random.choice(TO)
            if SUBJECT == "":
                subject = gen.sentence()
            if MSG == "":
                msg = gen.paragraph()
            send_mail(smtp_server, FROM, to, subject, msg, ATTACHEMENTS)
        elif action == ["read_mailbox_download_execute"]:
            read_mailbox_download_execute(imap_server, imap_login, imap_password)

