import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from smtplib import SMTP

PRODUCTION_ENVIRONMENT_NAME = "prod"


class EmailService:
    def __init__(self, config):
        self.config = config

    def environment_specific_subject(self, subject):
        if self.config.ENVIRONMENT != PRODUCTION_ENVIRONMENT_NAME:
            subject = f"From {self.config.ENVIRONMENT} Environment: {subject}"
        return subject

    def environment_specific_to_email_addresses(self, to_email_addresses):
        if self.config.ENVIRONMENT != PRODUCTION_ENVIRONMENT_NAME:
            to_email_addresses = self.config.NON_PROD_EMAIL_RECEIVER_ADDRESSES
        return to_email_addresses

    def add_non_prod_messaging_if_not_production(self, message, to_email_addresses):
        if self.config.ENVIRONMENT != PRODUCTION_ENVIRONMENT_NAME:
            message += "\n\n\n"
            message += "*" * 80
            message += "\n"
            message += "This email was sent from a non-production environment - "
            message += f"specifically the '{self.config.ENVIRONMENT}' environment."
            message += "\nas such, the target recipients were overridden to be the special set "
            message += "of non-prod recipients."
            message += "\n\nHad this been in the production environment, the following recipients "
            message += "would have received this email:"
            for next_address in to_email_addresses.split(","):
                message += f"\n\t{next_address}"

        # print(f"Message:\n{message}")
        return message

    async def send_email(self, to_email_addresses, message, subject, type="plain", use_ssl=True):
        # if isinstance(to_email_addresses, str):
        #     to_email_addresses = [
        #         next_email.strip() for next_email in to_email_addresses.split(",")
        #     ]
        # elif not isinstance(obj, list):
        #     to_email_addresses = [to_email_addresses]

        # original_to_email_addresses = to_email_addresses
        # to_email_addresses = self.environment_specific_to_email_addresses(to_email_addresses)

        print(f"Sending email to {to_email_addresses}")

        message_object = MIMEMultipart("alternative")
        message_object["Subject"] = self.environment_specific_subject(subject)
        message_object["From"] = self.config.SMTP_SENDER_EMAIL
        message_object["To"] = to_email_addresses

        # message = self.add_non_prod_messaging_if_not_production(
        #     message, original_to_email_addresses
        # )

        print(f"Message:\n{message}")

        if type == "html":
            body = MIMEText(message, "html")
        else:
            body = MIMEText(message, "plain")

        message_object.attach(body)

        with SMTP(self.config.SMTP_HOST, self.config.SMTP_PORT) as server:
            server.set_debuglevel(1)
            if use_ssl:
                server.starttls(context=ssl.create_default_context())
            server.login(user=self.config.SMTP_USERNAME, password=self.config.SMTP_PASSWORD)
            response = server.sendmail(
                self.config.SMTP_SENDER_EMAIL,
                to_email_addresses,
                message_object.as_string(),
            )
            if len(response) != 0:
                raise Exception(f"Email not sent - {response}")
        assert True
