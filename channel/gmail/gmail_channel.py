#!/usr/bin/env python3
import smtplib
import imaplib
import email
import re
import base64
import time
from random import randrange
from email.mime.text import MIMEText
from email.header import decode_header
from channel.channel import Channel
from concurrent.futures import ThreadPoolExecutor
from config import conf

smtp_ssl_host = 'smtp.gmail.com: 587'
imap_ssl_host = 'imap.gmail.com'
MAX_DELAY = 30
MIN_DELAY = 15
STEP_TIME = 2
LATESTN = 5
wait_time = 0
thread_pool = ThreadPoolExecutor(max_workers=8)

def checkEmail(email):
    # regex = '^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$'
    regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    if re.search(regex, email):
        return True
    else:
        return False

def process(max, speed):
    global wait_time
    i=0
    while i<=max:
        i=i+1
        time.sleep(speed)
        print("\r"+"Waited: "+str(i+wait_time)+"s", end='')
        # print("\r"+"==="*int(i-1)+":-)"+"==="*int(max-i)+"$"+str(max)+'  waited:'+str(i)+"%", end='')
    wait_time += max*speed
    
class GmailChannel(Channel):
    def __init__(self):
        self.host_email = conf().get('host_email')
        self.host_password = conf().get('host_password')
        self.to_addrs = conf().get('addrs_white_list')
        self.subject_keyword = conf().get('subject_keyword')
        
    def __exit__(self):
        pass
        
    def startup(self):
        global wait_time
        ques_list = list()
        lastques = {'from': None, 'subject': None, 'content': None}
        print("INFO: let's go...")
        while(True):
            ques_list = self.receiveEmail()
            if ques_list:
                for ques in ques_list:
                    if ques['subject'] is None:
                        print("WARN: question from:%s is empty " % ques['from'])
                    elif(lastques['subject'] == ques['subject'] and lastques['from'] == ques['from']):
                        print("INFO: this question has already been answered. Q:%s" % (ques['subject']))
                    else:
                        if ques['subject']:
                            print("Nice: a new message coming...", end='\n')
                            self.handle(ques) 
                            lastques = ques
                            wait_time = 0
                        else: 
                            print("WARN: the question in subject is empty")
            else: 
                process(randrange(MIN_DELAY, MAX_DELAY), STEP_TIME)
    
    def handle(self, question):
        message = dict()
        context = dict()
        print("INFO: From: %s Question: %s" % (question['from'], question['subject']))
        context['from_user_id'] = question['from']
        answer = super().build_reply_content(question['subject'], context) #get answer from openai
        message = MIMEText(answer)
        message['subject'] = question['subject']
        message['from'] = self.host_email
        message['to'] = question['from']
        thread_pool.submit(self.sendEmail, message)
        
    def sendEmail(self, message: list) -> dict:
        smtp_server = smtplib.SMTP(smtp_ssl_host)
        smtp_server.starttls()
        smtp_server.login(self.host_email, self.host_password)
        output = {'success': 0, 'failed': 0, 'invalid': 0}
        try:
            smtp_server.sendmail(message['from'], message['to'], message.as_string())
            print("sending to {}".format(message['to']))
            output['success'] += 1
        except Exception as e:
            print("Error: {}".format(e))
            output['failed'] += 1
        print("successed:{}, failed:{}".format(output['success'], output['failed']))
        smtp_server.quit()
        return output

    def receiveEmail(self):
        question_list = list()
        question = {'from': None, 'subject': None, 'content': None}
        imap_server = imaplib.IMAP4_SSL(imap_ssl_host)
        imap_server.login(self.host_email, self.host_password)
        imap_server.select('inbox')
        status, data = imap_server.search(None, 'ALL')
        mail_ids = []
        for block in data:
            mail_ids += block.split()
        #only fetch the latest 5 messages
        mail_ids = mail_ids[-LATESTN:]
        for i in mail_ids:
            status, data = imap_server.fetch(i, '(RFC822)')
            for response in data:
                if isinstance(response, tuple):
                    message = email.message_from_bytes(response[1])
                    mail_from = message['from'].split('<')[1].replace(">", "")
                    #TODO add check when not in white list
                    # if mail_from not in self.to_addrs:
                    #     continue
                    
                    #subject do not support chinese
                    mail_subject = decode_header(message['subject'])[0][0]
                    if isinstance(mail_subject, bytes):
                        # UnicodeDecodeError: 'utf-8' codec can't decode byte 0xc5
                        try:
                            mail_subject = mail_subject.decode()
                        except UnicodeDecodeError:
                            mail_subject = mail_subject.decode('latin-1')
                    if not self.check_contain(mail_subject, self.subject_keyword):   #check subject here
                        continue
                    if message.is_multipart(): 
                        mail_content = ''
                        for part in message.get_payload():
                            flag=False
                            if isinstance(part.get_payload(), list): 
                                    part = part.get_payload()[0]
                                    flag = True
                            if part.get_content_type()  in ['text/plain', 'multipart/alternative']: 
                                #TODO some string can't be decode
                                if flag:
                                    mail_content += str(part.get_payload())
                                else: 
                                    try:
                                        mail_content += base64.b64decode(str(part.get_payload())).decode("utf-8")
                                    except UnicodeDecodeError:
                                        mail_content += base64.b64decode(str(part.get_payload())).decode('latin-1')
                    else:
                        mail_content = message.get_payload()
                    question['from'] = mail_from
                    question['subject'] = ' '.join(mail_subject.split(' ')[1:])
                    question['content'] = mail_content
                    # print(f'\nFrom: {mail_from}')
                    print(f'\n\nSubject: {mail_subject}')
                    # print(f'Content: {mail_content.replace(" ", "")}')
                    question_list.append(question)
                    question = {'from': None, 'subject': None, 'content': None}
                    imap_server.store(i, "+FLAGS", "\\Deleted") #delete the mail i
                    print("INFO: deleting mail: %s" % mail_subject)
        imap_server.expunge()
        imap_server.close()
        imap_server.logout()
        return question_list
    
    def check_contain(self, content, keyword_list):
        if not keyword_list:
            return None
        for ky in keyword_list:
            if content.find(ky) != -1:
                return True
        return None 
        







