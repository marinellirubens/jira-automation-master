"""Module to test automation_service.email"""
from automation_service import email
from unittest import mock
import smtplib
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email import encoders


def test_email_sender_class():
    """Test the email sender constructor"""
    sender = email.EmailSender()

    assert isinstance(sender, email.EmailSender)
    assert sender.port is not None
    assert sender.smtp_server is not None
    assert sender.sender_email is not None


@mock.patch('builtins.print')
@mock.patch("smtplib.SMTP")
def test_send_email(email_mock: mock.MagicMock, mock_print: mock.MagicMock):
    """Test the send_email method"""
    email_mock.sendmail.side_effect = smtplib.SMTPRecipientsRefused('')
    receiver_email = ["teste@gmail.com"]
    sender = email.EmailSender(smtp_server="smtp.gmail.com", port=587, sender_email="")
    sender.send_email(receiver_email, "teste")

    mock_print.assert_called_once()
    email_mock.assert_called_once()
    assert email_mock.call_count == 1
    # TODO: Included mocking of the sendmail method


def test_message_builder_class_without_args():
    """Test the message builder constructor"""
    message_builder = email.MessageBuilder()

    assert isinstance(message_builder, email.MessageBuilder)
    assert message_builder.message is not None
    assert isinstance(message_builder.message, MIMEMultipart)
    assert message_builder.message.get_content_type() == "multipart/mixed"


def test_message_builder_class_with_args():
    """Test the message builder constructor with args"""
    message_builder = email.MessageBuilder(
        subject="subject",
        body="body",
        sender_email="sender_email",
        receiver_email="receiver_email",
        bcc_emails="bcc_emails",
        mime_type="plain"
    )

    assert isinstance(message_builder, email.MessageBuilder)
    assert message_builder.message["from"] == "sender_email"
    assert message_builder.message["to"] == "receiver_email"
    assert message_builder.message["Bcc"] == "bcc_emails"
    assert message_builder.message["Subject"] == "subject"
    assert message_builder.message.get_content_type() == "multipart/mixed"
    message_body = message_builder.message.get_payload()[0]
    assert message_body.get_content_type() == "text/plain"
    assert message_body.get_payload() == "body"


def test_set_sender_email():
    """Test the set_sender_email method"""
    message_sender = email.MessageBuilder()
    message_sender.set_sender_email("teste@teste.com")

    assert message_sender.message["From"] == "teste@teste.com"


def test_set_receiver_email():
    """Test the set_receiver_email method"""
    message_sender = email.MessageBuilder()
    message_sender.set_receiver_email("test@gmail.com")

    assert message_sender.message["To"] == "test@gmail.com"


def test_set_bcc_emails():
    """Test the set_bcc_emails method"""
    message_sender = email.MessageBuilder()
    message_sender.set_bcc_emails("test@gmail.com")

    assert message_sender.message["Bcc"] == "test@gmail.com"


def test_set_subject():
    """Test the set_subject method"""
    message_sender = email.MessageBuilder()
    message_sender.set_subject("subject")

    assert message_sender.message["Subject"] == "subject"


def test_set_message_body():
    """Test the set_message_body method"""
    message_sender = email.MessageBuilder()

    message_sender.set_message_body("body", "plain")

    assert message_sender.message.get_payload()[1].get_payload() == "body"
    assert message_sender.message.get_payload()[1].get_content_type() == "text/plain"

    with mock.patch.object(message_sender.message, 'attach') as mock_mime_text:
        message_sender.set_message_body("body", "plain")

        mock_mime_text.assert_called_once()


def test_add_attachments():
    """Test the add_attachments method"""
    message_sender = email.MessageBuilder()
    message_sender.set_subject("subject")
    message_sender.set_receiver_email("")

    attachments = {
        'teste.txt': b'teste',
        'teste2.txt': b'teste',
    }
    message_sender.add_attachments(attachments=attachments)
    payload = message_sender.message.get_payload()
    assert payload.__len__() == 3
    assert isinstance(payload[1], MIMEBase)
    assert payload[1].get_content_type() == 'application/octet-stream'

    assert isinstance(payload[2], MIMEBase)
    assert payload[2].get_content_type() == 'application/octet-stream'


def test_message_build():
    """Test the message_build method"""
    message_sender = email.MessageBuilder()
    message_sender.set_message_body("body", "plain")
    message_sender.set_subject("subject")
    message_sender.set_receiver_email("")
    message_build = message_sender.build()
    assert message_build == message_sender.message.as_string()
