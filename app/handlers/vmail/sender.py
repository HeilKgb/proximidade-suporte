"""
Copyright(C) Venidera Research & Development, Inc - All Rights Reserved
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
Written by Marcos Leone Filho <marcos@venidera.com>
"""

import smtplib
from os.path import basename
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.header import Header
from email.utils import parseaddr
import logging
from vmail.lib import config


def create_attachment(attach_files):
    """ Create a list of email attachments """
    attach_list = list()
    for attach in attach_files:
        with open(attach, 'rb') as myattach:
            part = MIMEApplication(
                myattach.read(),
                Name=basename(attach)
            )
        # After the file is closed
        part['Content-Disposition'] = 'attachment; filename="%s"' % basename(
            attach)
        attach_list.append(part)
    return attach_list


def send_email(toaddr, subject, message,
               fromaddr='suporte@venidera.com',
               is_html=False, config_name='aws', attach_files=None):
    """ Method to send email """
    cur_config = config.get_config(config_name=config_name)
    if is_html:
        message_type = 'html'
    else:
        message_type = 'plain'
    if attach_files and isinstance(attach_files, list):
        attachments = create_attachment(attach_files)
    elif attach_files and isinstance(attach_files, str):
        attachments = create_attachment([attach_files])
    else:
        attachments = list()
    logging.info('Sending email as %s message...', message_type)
    msg_root = MIMEMultipart('related')
    # msg.set_charset('utf8')
    logging.debug('Composing message to: %s', toaddr)
    fromaddr = parseaddr(fromaddr)[1]
    if not fromaddr:
        raise Exception('Invalid fromaddr. '
                        'fromaddr must be a valid email string')
    msg_root['From'] = fromaddr
    if type(toaddr) is list:
        msg_root['To'] = ", ".join(toaddr)
    else:
        msg_root['To'] = toaddr
    msg_root['Subject'] = Header(subject, 'utf-8')
    msg = MIMEMultipart()
    msg_root.attach(msg)
    _attach = MIMEText(message.encode('utf-8'), message_type, 'UTF-8')
    msg.attach(_attach)
    # attach files if exist:
    for _attach in attachments:
        msg_root.attach(_attach)
    logging.debug('Connecting to SMTP server...')
    server = smtplib.SMTP(
        host=cur_config['smtp_server'],
        port=cur_config['smtp_port'],
        timeout=10
    )
    server.set_debuglevel(0)
    server.starttls()
    server.ehlo()
    logging.debug('Logging into SMTP server...')
    server.login(cur_config['smtp_username'], cur_config['smtp_password'])
    logging.debug('Sending email...')
    server.sendmail(fromaddr,
                    toaddr,
                    msg_root.as_string().encode('utf-8'))
    server.quit()
    logging.info('Email sent to: %s', toaddr)
    return msg_root
