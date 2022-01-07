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

def smtp_connect(smtp_server, verbose=True):
    try:
        smtp = SMTP_SSL(host=smtp_server)
        smtp.ehlo()
        if verbose:
            print(Fore.GREEN+ " ==> [smtp_connect]   with SSL" +Style.RESET_ALL)
        return smtp
    except:
        try:
            smtp = SMTP(host=smtp_server)
            smtp.ehlo()
            if verbose:
                print(Fore.GREEN+ " ==> [smtp_connect]   without SSL" +Style.RESET_ALL)
            return smtp
        except:
            print(Fore.RED+ " ==> [smtp_connect]   failed!" +Style.RESET_ALL)
            return 1

def imap_connect(imap_server, username, password, verbose=True):
    try:
        imap = IMAP4_SSL(imap_server)
        imap.login(username, password)
        if verbose:
            print(Fore.GREEN+ " ==> [imap_connect]   with SSL" +Style.RESET_ALL)
        return imap
    except:
        try:
            imap = IMAP4(imap_server)
            imap.login(username, password)
            if verbose:
                print(Fore.GREEN+ " ==> [imap_connect]   without SSL" +Style.RESET_ALL)
            return imap
        except:
            print(Fore.RED+ " ==> [imap_connect]   failed!" +Style.RESET_ALL)

def send_mail(smtp_server, FROM="", TO="", subject="", msg="", attachements=[], verbose=True):
    smtp = smtp_connect(smtp_server, verbose=False)
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
    try:
        smtp.sendmail(mail["From"], mail["To"], mail.as_string())
        if verbose:
            print(Fore.GREEN+ " ==> [send_mail] "+mail["From"]+" --> "+mail["To"]+"  {"+subject+"}   -- "+ time.strftime("%H:%M:%S", time.localtime()) +Style.RESET_ALL)
        smtp_logout(smtp, verbose=False)
    except Exception as e:
        print(Fore.RED+ " ==> [send_mail] failed!  "+mail["From"]+" --> "+mail["To"]+"  -- "+ time.strftime("%H:%M:%S", time.localtime()) +Style.RESET_ALL)
        print(Fore.RED+str(e)+Style.RESET_ALL)
        smtp_logout(smtp, verbose=False)

def read_mailbox(imap_server, username, password, verbose=True): # attribut [ _payload ]
    imap = imap_connect(imap_server, username, password, verbose=False)
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
    print(Fore.GREEN+ " ==> [read_mailbox] {"+str(len(mails)-1)+"}   -- "+ time.strftime("%H:%M:%S", time.localtime()) +Style.RESET_ALL)
    imap_logout(imap, verbose=False)

def download_attachements(imap_server, username, password, verbose=True):
    imap = imap_connect(imap_server, username, password, verbose=False)
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
    imap_logout(imap, verbose=False)
    print(Fore.GREEN+ " ==> [download_attachements]   --- " + time.strftime("%H:%M:%S", time.localtime())+Style.RESET_ALL)

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

def delete_emails(imap, mails):
    for mail in mails:
        imap.store(mail,"+FLAGS","\\Deleted")
    imap.expunge()

def delete_all_emails(imap_server, username, password, verbose=True):
    imap = imap_connect(imap_server, username, password, verbose=False)
    delete_messages = []
    imap.select("INBOX")
    status, mails = imap.search(None, "ALL")
    for mail in mails[0].split():
        delete_messages.append(mail)
    delete_emails(imap, delete_messages)
    status, mails = imap.search(None, "ALL")
    if len(mails) == 1:
        print(Fore.GREEN+ " ==> [delete_all_emails]   was successfull   --- " + time.strftime("%H:%M:%S", time.localtime()) +Style.RESET_ALL)
        imap_logout(imap, verbose=False)
        return 0
    print(Fore.RED+ " ==> [delete_all_emails]   failed!   --- " + time.strftime("%H:%M:%S", time.localtime()) +Style.RESET_ALL)
    imap_logout(imap, verbose=False)
    return 1

def imap_logout(imap, verbose=True):
    try:
        imap.close()
        imap.logout()
        if verbose:
            print(Fore.GREEN+ " ==> [imap_logout]   was successfull" +Style.RESET_ALL)
    except:
        print(Fore.RED+ " ==> [imap_logout]   failed" +Style.RESET_ALL)

def smtp_logout(smtp, verbose=True):
    try:
        smtp.quit()
        if verbose:
            print(Fore.GREEN+ " ==> [smtp_logout]   was successfull" +Style.RESET_ALL)
    except:
        print(Fore.RED+ " ==> [smtp_logout]   failed" +Style.RESET_ALL)
