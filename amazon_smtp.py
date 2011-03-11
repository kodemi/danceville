#!/usr/bin/python

import smtpd
import email
import asyncore
from boto.ses import SESConnection


class AmazonSMTPServer(smtpd.SMTPServer):
    amazonSES = SESConnection()

    def process_message(self, peer, mailfrom, rcpttos, data):
        data = email.message_from_string(data)
        # Amazon SES don't support 'Organization' header, which is created 
        # by email_template module
        if 'Organization' in data:
            del data['Organization']
        data = data.as_string()
        result = self.amazonSES.send_raw_email(mailfrom, data, rcpttos)        

server = AmazonSMTPServer(('127.0.0.1', 9090), None)
asyncore.loop()
