#! /usr/local/bin/python
import sys
import os
import re
from smtplib import SMTP_SSL as SMTP       # this invokes the secure SMTP protocol (port 465, uses SSL)
from email.mime.text import MIMEText

def send(**kwargs):
    auth = kwargs['auth']
    SMTPserver = auth['SMTPserver']
    USERNAME = auth['USERNAME']
    PASSWORD = auth['PASSWORD']
    #fail sender to username if not provided
    if('sender' in auth): sender = auth['sender']
    else: sender = auth['USERNAME']
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