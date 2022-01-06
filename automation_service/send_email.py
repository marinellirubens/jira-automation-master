"""Sends email"""
from __future__ import absolute_import

import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
# import ssl


class EmailSender:
    """Class to send emails"""

    def __init__(self, port: int = 25, smtp_server: str = "",
                 sender_email: str = ""):
        self.port = port
        self.smtp_server = smtp_server
        self.sender_email = sender_email

    def send_email(self, receiver_email: list, message: str):
        """Method to send the message using lg SMTP server
        :param receiver_email: receiver list
        :type receiver_email: list
        :param message: message that will be sent to receiver
        :type message: str
        """
        # context = ssl.create_default_context() # SSL context
        with smtplib.SMTP(self.smtp_server, self.port) as server:
            # server.login(sender_email, password)
            print(self.sender_email, receiver_email)
            server.sendmail(self.sender_email, receiver_email, message)


class MessageBuilder:
    """Class to build a message to be sent by EmailSender"""
    def __init__(self, subject: str = "", body: str = "", sender_email: str = "",
                 receiver_email: str = "", bcc_emails: str = "", mime_type: str = "plain") -> None:
        self.message = MIMEMultipart()
        if sender_email:
            self.set_sender_email(sender_email)
        if receiver_email:
            self.set_receiver_email(receiver_email)
        if subject:
            self.set_subject(subject)
        if bcc_emails:
            self.set_bcc_emails(bcc_emails)

        self.message.attach(MIMEText(body, mime_type))

    def set_sender_email(self, sender_email: str):
        """Set the email sender

        :param sender_email: sender mail list separated by ; as str
        :type sender_email: str
        :return: self
        """
        self.message["From"] = sender_email

        return self

    def set_receiver_email(self, receiver_email: str):
        """set receiver mail list

        :param receiver_email: receiver mail list separated by ; as str
        :type receiver_email: str
        :return: self
        """
        self.message["To"] = receiver_email

        return self

    def set_bcc_emails(self, bcc_emails: str):
        """set blank copy mail list

        :param bcc_emails: blank copy mail list separated by ; as str
        :type bcc_emails: str
        :return: self
        """
        self.message["Bcc"] = bcc_emails

        return self

    def set_subject(self, subject: str):
        """Set subject of the email

        :param subject: mail subject
        :type subject: str
        :return: self
        """
        self.message["Subject"] = subject

        return self

    def set_message_body(self, message_body: str, mime_type: str = "plain"):
        """Set the message body

        :param message_body: text or html with the message body
        :type message_body: str
        :param mime_type: type of body, plain/html
        :type mime_type: str
        :return: self
        """
        self.message.attach(MIMEText(message_body, mime_type))

        return self

    def add_attachments(self, attachments: dict):
        """Add attachments to the email

        :param attachments: attachments dictionary where the key is the
            name of the file and the value is
            a binary with file content
        :type attachments: dict
        :return: self
        """
        for key in attachments.keys():
            filename = str(key)
            attachment = attachments[key]

            part = MIMEBase("application", "octet-stream")
            part.set_payload(attachment)

            # Encode file in ASCII characters to send by email
            encoders.encode_base64(part)

            # Add header as key/value pair to attachment part
            part.add_header(
                "Content-Disposition",
                f"attachment; filename= {filename}",
            )

            # Add attachment to message and convert message to string
            self.message.attach(part)

        return self

    def build(self) -> str:
        """Build the message to be sent

        :return: message as string
        :rtype: str
        """
        return self.message.as_string()
