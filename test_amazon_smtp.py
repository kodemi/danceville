#!/usr/bin/python

import smtplib
import email.utils
from email.mime.text import MIMEText

msg = MIMEText('test')
msg['To'] = email.utils.formataddr(('Deniska', 'dkonchekov@gmail.com'))
msg['From'] = email.utils.formataddr(('Author', 'dkonchekov@gmail.com'))
msg['Subject'] = 'test message'

server = smtplib.SMTP('127.0.0.1', 9090)
try:
    server.sendmail('dkonchekov@gmail.com', ['dkonchekov@gmail.com'], msg.as_string())
finally:
    server.quit()
