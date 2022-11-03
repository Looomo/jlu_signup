# -*- coding: UTF-8 -*-

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header

def mail(subject = "Recorder" , context = "" , receiver = "receiver@receiver.com"):
    # return None or set receiver=None if you need no notification
    if receiver == "" :
        return;
    server = 'smtp.qq.com'
    user = 'qq_account'
    passwd = 'smtp password'

    sender = 'qq_account@qq.com'
    receivers = [receiver]
    message = MIMEMultipart()
    message['From'] = Header(subject, 'utf-8')
    message['To'] = Header("mail box", 'utf-8')

    message['Subject'] = Header(subject, 'utf-8')

    message.attach(MIMEText(context, 'plain', 'utf-8'))



    try:
        smtpObj = smtplib.SMTP()
        smtpObj.connect(server, 25)  
        smtpObj.login(user, passwd)
        smtpObj.sendmail(sender, receivers, message.as_string())
        # print("mail send success")
    except smtplib.SMTPException:
        print('Error: failed to send email')
