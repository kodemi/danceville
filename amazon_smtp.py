#!/usr/bin/python

import smtpd
import email
import asyncore
from boto.ses import SESConnection


class AmazonSMTPServer(smtpd.SMTPServer):
    amazonSES = SESConnection()

    def process_message(self, peer, mailfrom, rcpttos, data):
        #message = EmailMessage()
        #message.subject = 'test'
        #message.bodyText = data
        data = email.message_from_string(data)
        if 'Organization' in data:
            del data['Organization']
        data = data.as_string()
        print "peer: ", peer
        print "mailfrom: ", mailfrom
        print "rcpttos: ", rcpttos
        print "data: ", data

        result = self.amazonSES.send_raw_email(mailfrom, data, rcpttos)        

server = AmazonSMTPServer(('127.0.0.1', 9090), None)
asyncore.loop()
