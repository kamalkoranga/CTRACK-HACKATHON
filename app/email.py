import os
from threading import Thread
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from flask import current_app


def send_async_email(app, subject, sender, recipients, text_body, html_body):
    with app.app_context():
        configuration = sib_api_v3_sdk.Configuration()
        configuration.api_key['api-key'] = app.config["BREVO_API_KEY"]

        api_instance = sib_api_v3_sdk.TransactionalEmailsApi(
            sib_api_v3_sdk.ApiClient(configuration)
        )

        email = sib_api_v3_sdk.SendSmtpEmail(
            sender={"email": sender},
            to=[{"email": r} for r in recipients],
            subject=subject,
            html_content=html_body,
            text_content=text_body,
        )

        try:
            api_instance.send_transac_email(email)
        except ApiException as e:
            app.logger.error(f"Brevo email error: {e}")


def send_email(subject, sender, recipients, text_body, html_body):
    app = current_app._get_current_object()
    Thread(
        target=send_async_email,
        args=(app, subject, sender, recipients, text_body, html_body),
        daemon=True
    ).start()
