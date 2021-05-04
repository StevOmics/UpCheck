#! /usr/local/bin/python
import sys
import os
import re

from smtplib import SMTP_SSL as SMTP       # this invokes the secure SMTP protocol (port 465, uses SSL)
from email.mime.text import MIMEText

def send(**kwargs):
    SMTPserver = kwargs['auth']['SMTPserver']
    sender = kwargs['auth']['sender']
    USERNAME = kwargs['auth']['USERNAME']
    PASSWORD = kwargs['auth']['PASSWORD']
    text_subtype = 'plain'

    #compose message
    destination =kwargs['destination']
    content=kwargs['message']
    subject=kwargs['subject']
    msg = MIMEText(content, text_subtype)
    msg['Subject']= subject
    msg['From']   = sender # some SMTP servers will do this automatically, not all

    conn = SMTP(SMTPserver)
    conn.set_debuglevel(False)
    conn.login(USERNAME, PASSWORD)
    try:
        conn.sendmail(sender, destination, msg.as_string())
    finally:
        conn.quit()