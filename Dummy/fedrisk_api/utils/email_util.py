# from Riskuity_api.service.email_service import EmailService
from fedrisk_api.utils.ses import EmailService


# def get_email_template(template_name, type="plain"):
#     template_type = "html" if type == "html" else "txt"
#     with open(f"./Riskuity_api/templates/email/{template_name}/subject.{template_type}") as pr:
#         subject = pr.read().strip()

#     with open(f"./Riskuity_api/templates/email/{template_name}/body.{template_type}") as pr:
#         body = pr.read().strip()

#     return subject, body


async def send_invitation_email(
    # email_service: EmailService,
    user_email_data,
    # type="plain"
):
    # subject, body = get_email_template(template_name="invitation_email", type=type)
    # for user in user_email_data:
    #     body = body.format(link=user["link"])
    #     await email_service.send_email(
    #         to_email_addresses=user["email"],
    #         message=body,
    #         subject=subject,
    #         type=type,
    #     )
    for user in user_email_data:
        new_line = "\n"
        body = f'Signup Link : {user["link"]}{new_line}Best Regards,{new_line}Riskuity Team'
        EmailService().send_email(
            to_email=user["email"],
            subject="Signup Invitation Link",
            message=body,
        )


# async def send_otp_email(
# email_service: EmailService,
# user_otp_data,
# type="plain"
# ):
# subject, body = get_email_template(template_name="tenant_registration_otp", type=type)
# body = body.format(otp=user_otp_data["otp"])
# await email_service.send_email(
#     to_email_addresses=user_otp_data["email"],
#     message=body,
#     subject=subject,
#     type=type,
# )
# new_line = "\n"
# body = f'Hello,{new_line}Please use the verification code below on the Riskuity : {user_otp_data["otp"]}{new_line}If you did not request this, you can ignore this email or let us know.{new_line}Best Regards{new_line}Riskuity Team'
# EmailService().send_email(
#     to_email=user_otp_data["email"],
#     subject="Signup OTP Code",
#     message=body,
# )


async def send_signup_success_email(
    # email_service: EmailService,
    user_signup_data,
    # type="plain"
):
    # subject, body = get_email_template(template_name="signup", type=type)
    # body = body.format(name=user_signup_data["name"])
    # await email_service.send_email(
    #     to_email_addresses=user_signup_data["email"], message=body, subject=subject, type=type
    # )
    new_line = "\n"
    body = f'Dear {user_signup_data["name"]},{new_line}Thank you for signing up for our service! We are excited to have you on board and hope that you find our service useful.{new_line}If you have any questions or need help getting started, please do not hesitate to reach out. Our customer support team is always happy to assist.{new_line}Best Regards{new_line}Riskuity Team'
    EmailService().send_email(
        to_email=user_signup_data["email"],
        subject="Riskuity Signup Welcome Email",
        message=body,
    )


async def send_payment_success_email(
    # email_service: EmailService,
    payment_success_data,
    # type="plain"
):
    # subject, body = get_email_template(template_name="payment_success", type=type)

    # await email_service.send_email(
    #     to_email_addresses=payment_success_data["email"],
    #     message=body,
    #     subject=subject,
    #     type=type,
    # )
    new_line = "\n"
    body = f"Thank you for your payment!{new_line}Your transaction has been successfully processed.{new_line}If you have any questions, please do not hesitate to reach out. Our customer support team is always happy to assist.{new_line}Best Regards{new_line}Riskuity Team"
    EmailService().send_email(
        to_email=payment_success_data["email"],
        subject="Riskuity Subscription | Payment Success",
        message=body,
    )


async def send_payment_failure_email(
    # email_service: EmailService,
    payment_fail_data,
    # type="plain"
):
    # subject, body = get_email_template(template_name="payment_fail", type=type)

    # await email_service.send_email(
    #     to_email_addresses=payment_fail_data["email"],
    #     message=body,
    #     subject=subject,
    #     type=type,
    # )
    new_line = "\n"
    body = f"Your recent transaction for renewal of your Riskuity subscription has been declined.{new_line}Please double check your payment/billing information and try again or contact our customer support team for assistance.{new_line}If you have any questions, please do not hesitate to reach out. Our customer support team is always happy to assist.{new_line}Best Regards{new_line}Riskuity Team"
    EmailService().send_email(
        to_email=payment_fail_data["email"],
        subject="Riskuity Subscription | Payment Fail Notification",
        message=body,
    )


async def send_subscription_success_email(
    # email_service: EmailService,
    subscription_data,
    # type="plain"
):
    new_line = "\n"
    body = f'Your recent transaction for renewal of your Riskuity subscription has been declined.{new_line}Frequency : {subscription_data["frequency"]}{new_line}Start date : {subscription_data["start_date"]}{new_line}End date : {subscription_data["end_date"]}{new_line}Free Users : {subscription_data["free_users"]}{new_line}Additional Users : {subscription_data["additional_users"]}.{new_line}Best Regards{new_line}Riskuity Team'
    EmailService().send_email(
        to_email=subscription_data["email"],
        subject="Riskuity Subscription | Payment Fail Notification",
        message=body,
    )
    # subject, body = get_email_template(template_name="subscription_success", type=type)
    # body = body.format(
    #     start_date=subscription_data["start_date"],
    #     end_date=subscription_data["end_date"],
    #     free_users=subscription_data["free_users"],
    #     additional_users=subscription_data["additional_users"],
    #     frequency=subscription_data["frequency"],
    # )
    # await email_service.send_email(
    #     to_email_addresses=subscription_data["email"],
    #     message=body,
    #     subject=subject,
    #     type=type,
    # )


async def send_subscription_update_email(
    # email_service: EmailService,
    subscription_data,
    # type="plain"
):
    new_line = "\n"
    body = f'Your subscription with Riskuity is updated.{new_line}Your subscription id  : {subscription_data["subscription"]}{new_line}If you have any questions, please do not hesitate to reach out. Our customer support team is always happy to assist.{new_line}Best Regards{new_line}Riskuity Team'
    EmailService().send_email(
        to_email=subscription_data["email"],
        subject="Riskuity Subscription Updated",
        message=body,
    )
    # subject, body = get_email_template(template_name="subscription_update", type=type)
    # body = body.format(subscription=subscription_data["subscription"])
    # await email_service.send_email(
    #     to_email_addresses=subscription_data["email"],
    #     message=body,
    #     subject=subject,
    #     type=type,
    # )


async def send_subscription_cancel_email(
    # email_service: EmailService,
    subscription_fail_data,
    # type="plain"
):
    new_line = "\n"
    body = f'We have received notification that you have cancelled your subscription with subscription id: {subscription_fail_data["subscription"]} to our services{new_line}We are sorry to see you go and would like to thank you for your past support. If there is anything that we could have done differently, please let us know.{new_line}We hope to have the opportunity to serve you again in the future.{new_line}Best Regards{new_line}Riskuity Team'
    EmailService().send_email(
        to_email=subscription_fail_data["email"],
        subject="Riskuity Subscription Canceled",
        message=body,
    )
    # subject, body = get_email_template(template_name="subscription_cancel", type=type)
    # body = body.format(subscription=subscription_fail_data["subscription"])
    # await email_service.send_email(
    #     to_email_addresses=subscription_fail_data["email"],
    #     message=body,
    #     subject=subject,
    #     type=type,
    # )


async def send_control_exception_email(control_exception_data):
    emailstring = control_exception_data["emails"]
    emails = emailstring.split(",")
    if len(emails) > 0:
        for email in emails:
            EmailService().send_email(
                to_email=email,
                subject="You've been added to an exception on a control",
                message=f'Link: {control_exception_data["hyperlink"]}',
            )
    else:
        EmailService().send_email(
            to_email=email,
            subject="You've been added to an exception on a control",
            message=f'Link: {control_exception_data["hyperlink"]}',
        )


async def send_watch_email(email_data):
    new_line = "\n"
    body = f'You are receiving this notification as you have your email watch notifications switched on.{new_line}{email_data["message"]}{new_line}Best Regards{new_line}Riskuity Team'
    EmailService().send_email(
        to_email=email_data["email"],
        subject=email_data["subject"],
        message=body,
    )


async def send_assigned_to_email(email_data):
    new_line = "\n"
    body = f'You are receiving this notification as you have your email assigned notifications switched on.{new_line}{email_data["message"]}{new_line}Best Regards{new_line}Riskuity Team'
    EmailService().send_email(
        to_email=email_data["email"],
        subject=email_data["subject"],
        message=body,
    )


async def send_event_trigger_email(email_data):
    new_line = "\n"
    body = f'{email_data["email-body"]}{new_line}Best Regards{new_line}Riskuity Team'
    # Send single email
    EmailService().send_email(
        to_email=email_data["recipient_id"],
        subject=email_data["email-subject"],
        message=body,
    )

    # Send to internal cc list
    internal_ccs = email_data["internal_cc_recipient_list"]
    for internal_email in internal_ccs:
        EmailService().send_email(
            to_email=internal_email,
            subject=email_data["email-subject"],
            message=body,
        )

    # Send to external cc list
    external_ccs = email_data["external_cc_recipient_list"]
    for external_email in external_ccs:
        EmailService().send_email(
            to_email=external_email,
            subject=email_data["email-subject"],
            message=body,
        )


async def send_temp_password(email_data):
    new_line = "\n"
    body = f'You have requested to reset your password. Your confirmation code is: {new_line}{email_data["tmp_password"]}{new_line}Best Regards{new_line}Riskuity Team'
    EmailService().send_email(
        to_email=email_data["email"],
        subject=email_data["subject"],
        message=body,
    )


async def send_auditor_email(email_data):
    new_line = "\n"
    body = f'You are receiving this notification as you have been assigned as an auditor to Riskuity audit evidence. Please log in to Riskuity and review the audit evidence at the following location {email_data["link"]}{new_line}Best Regards{new_line}Riskuity Team'
    EmailService().send_email(
        to_email=email_data["email"],
        subject=email_data["subject"],
        message=body,
    )


async def send_evidence_rejected_email(email_data):
    new_line = "\n"
    body = f'You are receiving this notification as you have submitted audit evidence that has been rejected. Please log in to Riskuity and review the audit evidence at the following location {email_data["link"]}{new_line}Best Regards{new_line}Riskuity Team'
    EmailService().send_email(
        to_email=email_data["email"],
        subject=email_data["subject"],
        message=body,
    )
