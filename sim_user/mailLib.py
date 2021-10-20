import os
import time
import getpass
import email.mime.multipart
import email.mime.text
import email.mime.image
import email.mime.audio
from datetime import datetime
from pprint import pprint
from colorama import Style, Fore
from smtplib import SMTP, SMTP_SSL
from imaplib import IMAP4_SSL, IMAP4

def smtp_connect(smtp_server):
    try:
        smtp = SMTP_SSL(host=smtp_server)
        smtp.ehlo()
        return smtp
    except:
        try:
            smtp = SMTP(host=smtp_server)
            smtp.ehlo()
            return smtp
        except:
            print(Fore.RED+ "Can't connect to remote smtp server" +Style.RESET_ALL)
            return 1

def imap_connect(imap_server, username, password):
    try:
        imap = IMAP4_SSL(imap_server)
        imap.login(username, password)
        return imap
    except:
        try:
            imap = IMAP4(imap_server)
            imap.login(username, password)
            return imap
        except:
            print(Fore.RED+ "Can't connect to remote imap server" +Style.RESET_ALL)

def send_mail(smtp, FROM="", TO="", subject="", msg="", attachements=[]):
    mail = email.mime.multipart.MIMEMultipart()
    mail["Subject"] = "[ "+subject+" ]"
    mail["From"] = FROM
    mail["To"] = TO
    msg = email.mime.text.MIMEText(msg, _subtype="plain")
    msg.add_header("Content-Disposition", "email message")
    mail.attach(msg)
    
    for attachement in attachements:
        if attachement[0] == "image":
            img = email.mime.image.MIMEImage(open(attachement[1], "rb").read())
            img.add_header("Content-Disposition", "attachement")
            img.add_header("Attachement-type", "image")
            img.add_header("Attachement-filename", attachement[1])
            mail.attach(img)

        if attachement[0] == "file":
            text = email.mime.text.MIMEText(open(attachement[1], "r").read())
            text.add_header("Content-Disposition", "attachement")
            text.add_header("Attachement-type", "filetext")
            text.add_header("Attachement-filename", attachement[1])
            mail.attach(text)
    
    smtp.sendmail(mail["From"], mail["To"], mail.as_string())

def read_mailbox(imap): # attribut [ _payload ]
    mails = []
    imap.select("INBOX")
    status, mails = imap.search(None, "ALL")
    for mail in mails[0].split():
        status, data = imap.fetch(mail, "(RFC822)")
        mail_content = email.message_from_string(data[0][1].decode("utf-8"))
        mails.append(mail_content)
        for part in mail_content.walk():
            if not part.is_multipart():
                pass
    return mails

def download_attachements(imap):
    #INIT
    if not os.path.isdir("/home/"+getpass.getuser()+"/Downloads"):
        os.makedirs("/home/"+getpass.getuser()+"/Downloads")
    mails = []
    imap.select("INBOX")
    status, mails = imap.search(None, "ALL")
    for mail in mails[0].split():
        status, data = imap.fetch(mail, "(RFC822)")
        mail_content = email.message_from_string(data[0][1].decode("utf-8"))
        for part in mail_content.walk():
            if not part.is_multipart():
                if part["Content-Disposition"] == "attachement" and part["Attachement-type"] == "filetext":
                    username = getpass.getuser()
                    file = open(part["Attachement-filename"],"w")
                    file.write(part._payload)
                    file.close()

def delete_old_emails(imap, time_laps=60):
    delete_messages = []
    imap.select("INBOX")
    status, mails = imap.search(None, "ALL")
    for mail in mails[0].split():
        status, data = imap.fetch(mail, "(RFC822)")
        mail_content = email.message_from_string(data[0][1].decode("utf-8"))
        if (time.time() - time.mktime(time.strptime(mail_content["Date"], "%a, %d %b %Y %H:%M:%S %z")) >= time_laps ):
            delete_messages.append(mail)
    delete_emails(imap, delete_messages)

def delete_all_emails(imap):
    delete_messages = []
    imap.select("INBOX")
    status, mails = imap.search(None, "ALL")
    for mail in mails[0].split():
        delete_messages.append(mail)
    delete_emails(imap, delete_messages)

def delete_emails(imap, mails):
    for mail in mails:
        imap.store(mail,"+FLAGS","\\Deleted")
    imap.expunge()
