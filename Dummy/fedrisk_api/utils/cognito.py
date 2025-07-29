import base64
import hashlib
import hmac
import logging
import secrets
import string

import boto3
from botocore.exceptions import ClientError

from config.config import Settings

LOGGER = logging.getLogger(__name__)


def generate_password():
    """Generates a password with 8 characters, including at least one uppercase letter, one lowercase letter, one number, and one special character."""

    alphabet = string.ascii_letters + string.digits + string.punctuation

    while True:
        password = "".join(secrets.choice(alphabet) for i in range(8))
        if (
            any(c.islower() for c in password)
            and any(c.isupper() for c in password)
            and any(c.isdigit() for c in password)
            and any(c in string.punctuation for c in password)
        ):
            return password


print(generate_password())


def _cognito_username_from_email(email_address):
    return email_address.lower().replace("@", "_at_").replace(".", "dot")


class CognitoIdentityProviderWrapper:
    """Encapsulates Amazon Cognito actions"""

    def __init__(self, user_pool_id=None, client_id=None, client_secret=None):
        """
        :param user_pool_id: The ID of an existing Amazon Cognito user pool.
        :param client_id: The ID of a client application registered with the user pool.
        :param client_secret: The client secret, if the client has a secret.
        """
        settings = Settings()
        self.cognito_idp_client = boto3.client(
            "cognito-idp",
            region_name=settings.AWS_DEFAULT_REGION,
            aws_access_key_id=settings.COGNITO_ACCESS_KEY_ID,
            aws_secret_access_key=settings.COGNITO_SECRET_ACCESS_KEY,
        )
        self.user_pool_id = user_pool_id if user_pool_id else settings.COGNITO_USER_POOL_ID
        self.client_id = client_id = client_id if client_id else settings.COGNITO_WEB_CLIENT_ID
        self.client_secret = client_secret

    def sign_up_user(self, user_email, password, phone_number, first_name, last_name):
        try:
            kwargs = {
                "ClientId": self.client_id,
                "Username": _cognito_username_from_email(user_email),
                "Password": password,
                "UserAttributes": [
                    {"Name": "email", "Value": user_email},
                    {"Name": "phone_number", "Value": phone_number},
                    {"Name": "given_name", "Value": first_name},
                    {"Name": "family_name", "Value": last_name},
                ],
            }
            if self.client_secret is not None:
                kwargs["SecretHash"] = self._secret_hash(user_email)
            self.cognito_idp_client.sign_up(**kwargs)
            confirm_sign_up_response = self.cognito_idp_client.admin_confirm_sign_up(
                UserPoolId=self.user_pool_id, Username=_cognito_username_from_email(user_email)
            )
            LOGGER.info(f"confirm_sign_up_response {confirm_sign_up_response}")
            return confirm_sign_up_response["ResponseMetadata"]["HTTPStatusCode"] == 200
        except ClientError as err:
            if err.response["Error"]["Code"] == "UsernameExistsException":
                raise Exception("User already exists in User Pool with same email address")
            else:
                LOGGER.exception(f"Couldn't sign up {user_email}")
            raise

    def update_user_attributes(self, first_name, last_name, phone_no, access_token):
        try:
            kwargs = {
                "UserAttributes": [
                    {
                        "Name": "given_name",
                        "Value": first_name,
                    },
                    {
                        "Name": "family_name",
                        "Value": last_name,
                    },
                    {
                        "Name": "phone_number",
                        "Value": phone_no,
                    },
                ],
                "AccessToken": access_token,
            }

            cognito_user = self.cognito_idp_client.update_user_attributes(**kwargs)
            return cognito_user

        except ClientError as err:
            if err.response["Error"]["Code"] == "UsernameExistsException":
                raise Exception("User already exists in User Pool with same email address")
            else:
                LOGGER.exception(f"Could not retrieve user")
            raise

    def admin_get_user(self, email):
        try:
            kwargs = {
                # "ClientId": self.client_id,
                "UserPoolId": self.user_pool_id,
                "Username": _cognito_username_from_email(email),
            }
            if self.client_secret is not None:
                kwargs["SecretHash"] = self._secret_hash(email)
            cognito_user = self.cognito_idp_client.admin_get_user(**kwargs)
            return cognito_user

        except ClientError as err:
            if err.response["Error"]["Code"] == "UsernameExistsException":
                raise Exception("User already exists in User Pool with same email address")
            else:
                LOGGER.exception(f"Could not retrieve user")
            raise

    def _secret_hash(self, user_email):
        """
        Calculates a secret hash from a user email and a client secret.
        :param user_email: The email address to use when calculating the hash.
        :return: The secret hash.
        """
        key = self.client_secret.encode()
        msg = bytes(user_email + self.client_id, "utf-8")
        secret_hash = base64.b64encode(
            hmac.new(key, msg, digestmod=hashlib.sha256).digest()
        ).decode()
        return secret_hash

    async def authenticate_user(self, username, password):
        """
        Authenticates a user with a user email and password.
        :param username: The username of the user to authenticate.
        :param password: The password of the user to authenticate.
        :return: The authentication result or challenge.
        """
        LOGGER.info(f"Authenticating user {username}")
        try:
            kwargs = {
                "ClientId": self.client_id,
                "AuthFlow": "USER_PASSWORD_AUTH",
                "AuthParameters": {
                    "USERNAME": username,
                    "PASSWORD": password,
                },
            }

            if self.client_secret is not None:
                kwargs["AuthParameters"]["SECRET_HASH"] = self._secret_hash(username)

            response = self.cognito_idp_client.initiate_auth(**kwargs)
            LOGGER.info(response)

            if "AuthenticationResult" in response:
                return response["AuthenticationResult"]
            elif "ChallengeName" in response:
                return response.get("Session")
            else:
                LOGGER.warning("Unknown authentication response format")
                return None

        except ClientError as err:
            error_code = err.response["Error"]["Code"]
            if error_code == "NotAuthorizedException":
                LOGGER.exception("Invalid email or password")
            elif error_code == "UserNotFoundException":
                LOGGER.exception("User does not exist")
            elif error_code == "InvalidParameterException":
                LOGGER.exception("Username or password missing")
            else:
                LOGGER.exception(f"Couldn't authenticate {username}: {error_code}")
            raise

    # def authenticate_user(self, user_email, password):
    #     """
    #     Authenticates a user with a user email and password.
    #     :param user_email: The user email of the user to authenticate.
    #     :param password: The password of the user to authenticate.
    #     :return: The authentication result.
    #     """
    #     LOGGER.info(f"Authenticating user {user_email} with password {password}")
    #     try:
    #         kwargs = {
    #             "ClientId": self.client_id,
    #             "AuthFlow": "USER_PASSWORD_AUTH",
    #             "AuthParameters": {
    #                 "USERNAME": _cognito_username_from_email(user_email),
    #                 "PASSWORD": password,
    #             },
    #         }
    #         if self.client_secret is not None:
    #             kwargs["AuthParameters"]["SECRET_HASH"] = self._secret_hash(
    #                 _cognito_username_from_email(user_email)
    #             )
    #         response = self.cognito_idp_client.initiate_auth(**kwargs)
    #         LOGGER.info
    #         return response["AuthenticationResult"]
    #     except ClientError as err:
    #         if err.response["Error"]["Code"] == "NotAuthorizedException":
    #             LOGGER.exception("Invalid email or password")
    #         elif err.response["Error"]["Code"] == "UserNotFoundException":
    #             LOGGER.exception("User does not exists")
    #         elif err.response["Error"]["Code"] == "InvalidParameterException":
    #             LOGGER.exception("Email or password missing")
    #         else:
    #             LOGGER.exception(f"Couldn't authenticate {user_email}")
    #         raise

    def admin_update_user_pasword(self, email, password, token):
        try:
            kwargs = {
                # "ClientId": self.client_id,
                "UserPoolId": self.user_pool_id,
                "Username": _cognito_username_from_email(email),
                "Password": password,
                "Permanent": True,
            }

            cognito_user = self.cognito_idp_client.admin_set_user_password(**kwargs)
            return cognito_user

        except ClientError as err:
            if err.response["Error"]["Code"] == "UsernameExistsException":
                raise Exception("User already exists in User Pool with same email address")
            else:
                LOGGER.exception(f"Could not retrieve user")
            raise

    async def admin_set_temp_user_pasword(self, email):
        try:
            temp_password = generate_password()
            username = _cognito_username_from_email(email)

            # Set temporary password (non-permanent)
            self.cognito_idp_client.admin_set_user_password(
                UserPoolId=self.user_pool_id,
                Username=username,
                Password=temp_password,
                Permanent=False,
            )

            # Initiate auth
            auth_response = await self.authenticate_user(username, temp_password)

            # if isinstance(auth_response, str):
            #     # Challenge issued; respond with NEW_PASSWORD
            #     final_password = generate_password()  # real password user will set
            #     challenge_response = self.cognito_idp_client.respond_to_auth_challenge(
            #         ClientId=self.client_id,
            #         ChallengeName="NEW_PASSWORD_REQUIRED",
            #         Session=auth_response,
            #         ChallengeResponses={
            #             "USERNAME": username,
            #             "NEW_PASSWORD": final_password,
            #         },
            #     )
            #     LOGGER.info("Completed NEW_PASSWORD_REQUIRED challenge")
            #     return {
            #         "temp_password": final_password,
            #         "auth_token": challenge_response.get("AuthenticationResult")
            #     }

            return {
                "temp_password": temp_password,
                "authorization": {"auth_token": auth_response, "username": username},
            }

        except ClientError as err:
            if err.response["Error"]["Code"] == "UsernameExistsException":
                raise Exception("User already exists in User Pool with same email address")
            else:
                LOGGER.exception("Could not set temporary password")
            raise

    def change_user_password(self, user_email, old_password, new_password, user_access_token):
        """
        Change the password of a user after authenticating the user.
        :param user_email: The user email address of the user to authenticate.
        :param old_password: The password of the user to authenticate.
        :param new_password: The new password to set for the user
        """

        try:
            result = self.cognito_idp_client.change_password(
                PreviousPassword=old_password,
                ProposedPassword=new_password,
                AccessToken=user_access_token,
            )
            return result

        except ClientError as err:
            if err.response["Error"]["Code"] == "NotAuthorizedException":
                LOGGER.exception("Invalid email_address or password")
            elif err.response["Error"]["Code"] == "UserNotFoundException":
                LOGGER.exception("User does not exist")
            elif err.response["Error"]["Code"] == "InvalidParameterException":
                LOGGER.exception("Email Address or password missing")
            else:
                LOGGER.exception(f"Couldn't authenticate {user_email}")
            raise

    def user_forgot_password(self, user_email):
        username = _cognito_username_from_email(user_email)

        try:
            result = self.cognito_idp_client.forgot_password(
                ClientId=self.client_id,
                Username=username,
            )
            LOGGER.info(result)
            return result

        except ClientError as err:
            if err.response["Error"]["Code"] == "NotAuthorizedException":
                LOGGER.exception("Invalid email_address or password")
            elif err.response["Error"]["Code"] == "UserNotFoundException":
                LOGGER.exception("User does not exist")
            elif err.response["Error"]["Code"] == "InvalidParameterException":
                LOGGER.exception("Email Address or password missing")
            else:
                LOGGER.exception(f"Couldn't authenticate {user_email}")
            raise

    def user_confirm_forgot_password(self, user_email, confirmation_code, password):
        username = _cognito_username_from_email(user_email)

        try:
            result = self.cognito_idp_client.confirm_forgot_password(
                ClientId=self.client_id,
                Username=username,
                ConfirmationCode=confirmation_code,
                Password=password,
            )
            return result

        except ClientError as err:
            if err.response["Error"]["Code"] == "NotAuthorizedException":
                LOGGER.exception("Invalid email_address or password")
            elif err.response["Error"]["Code"] == "UserNotFoundException":
                LOGGER.exception("User does not exist")
            elif err.response["Error"]["Code"] == "InvalidParameterException":
                LOGGER.exception("Email Address or password missing")
            else:
                LOGGER.exception(f"Couldn't authenticate {user_email}")
            raise

    def get_user(self, access_token):
        try:
            result = self.cognito_idp_client.get_user(AccessToken=access_token)
            return result

        except ClientError as err:
            if err.response["Error"]["Code"] == "NotAuthorizedException":
                LOGGER.exception("Invalid email_address or password")
            elif err.response["Error"]["Code"] == "UserNotFoundException":
                LOGGER.exception("User does not exist")
            elif err.response["Error"]["Code"] == "InvalidParameterException":
                LOGGER.exception("Email Address or password missing")
            else:
                LOGGER.exception(f"Couldn't authenticate using access token")
            raise

    def resend_confirmation_code(self, username):
        try:
            cognito_resend = self.cognito_idp_client.resend_confirmation_code(
                ClientId=self.client_id, Username=username
            )
            return cognito_resend

        except ClientError as err:
            if err.response["Error"]["Code"] == "NotAuthorizedException":
                LOGGER.exception("Invalid username")
            elif err.response["Error"]["Code"] == "UserNotFoundException":
                LOGGER.exception("User does not exist")
            elif err.response["Error"]["Code"] == "InvalidParameterException":
                LOGGER.exception("Username missing")
            else:
                LOGGER.exception(f"Couldn't authenticate using access token")
            raise

    def confirm_signup(self, client_id, username, confirmation_code):
        try:
            cognito_confirm = self.cognito_idp_client.confirm_sign_up(
                ClientId=client_id,
                Username=username,
                ConfirmationCode=confirmation_code,
            )
            return cognito_confirm

        except ClientError as err:
            if err.response["Error"]["Code"] == "NotAuthorizedException":
                LOGGER.exception("Invalid email_address or password")
            elif err.response["Error"]["Code"] == "UserNotFoundException":
                LOGGER.exception("User does not exist")
            elif err.response["Error"]["Code"] == "InvalidParameterException":
                LOGGER.exception("Email Address or password missing")
            else:
                LOGGER.exception(f"Couldn't confirm signup using code")
            raise

    def verify_password(self, email, password):
        """
        Verifies a user's password against a Cognito User Pool.

        Args:
            username (str): The username of the user.
            password (str): The password to verify.
            user_pool_id (str): The ID of the User Pool.
            client_id (str): The ID of the App Client.

        Returns:
            bool: True if the password is correct, False otherwise.
            Raises exceptions if there are issues with Cognito or the client.
        """
        try:
            kwargs = {
                "UserPoolId": self.user_pool_id,
                "ClientId": self.client_id,
                "AuthFlow": "ADMIN_USER_PASSWORD_AUTH",
                "AuthParameters": {
                    "USERNAME": _cognito_username_from_email(email),
                    "PASSWORD": password,
                },
            }
            # Initiate authentication using the username and password
            response = self.cognito_idp_client.admin_initiate_auth(**kwargs)
            LOGGER.info(response)

            # Check if the authentication was successful
            if "Session" in response:
                return response  # Password is correct
            else:
                return False  # Password is incorrect

        except ClientError as e:
            print(f"Error verifying password: {e}")
            return False

    ######## MFA ##################

    def start_sign_in(self, user_email, password):
        try:
            kwargs = {
                "UserPoolId": self.user_pool_id,
                "ClientId": self.client_id,
                "AuthFlow": "ADMIN_USER_PASSWORD_AUTH",
                "AuthParameters": {
                    "USERNAME": _cognito_username_from_email(user_email),
                    "PASSWORD": password,
                },
            }
            if self.client_secret is not None:
                kwargs["AuthParameters"]["SECRET_HASH"] = self._secret_hash(
                    _cognito_username_from_email(user_email)
                )

            response = self.cognito_idp_client.admin_initiate_auth(**kwargs)
            LOGGER.info(response)

            challenge_name = response.get("ChallengeName", None)

            if challenge_name == "MFA_SETUP":
                # user needs to set up TOTP
                if "SOFTWARE_TOKEN_MFA" in response["ChallengeParameters"].get(
                    "MFAS_CAN_SETUP", ""
                ):
                    mfa_data = self.get_mfa_secret(response["Session"])
                    return {
                        "status": "MFA_SETUP_REQUIRED",
                        "session": mfa_data["Session"],
                        "secret_code": mfa_data["SecretCode"],
                    }

            if challenge_name == "SOFTWARE_TOKEN_MFA":
                return {"status": "TOTP_MFA", "session": response["Session"]}

            if challenge_name == "SMS_MFA":
                return {
                    "status": "SMS_MFA",
                    "session": response["Session"],
                    "delivery": response["ChallengeParameters"].get("CODE_DELIVERY_DESTINATION"),
                    "username": response["ChallengeParameters"].get("USER_ID_FOR_SRP"),
                }

            if challenge_name == "EMAIL_OTP":
                return {
                    "status": "EMAIL_OTP",
                    "session": response["Session"],
                    "delivery": response["ChallengeParameters"].get("CODE_DELIVERY_DESTINATION"),
                    "username": response["ChallengeParameters"].get("USER_ID_FOR_SRP"),
                }

            elif "AuthenticationResult" in response:
                return {"status": "SUCCESS", "auth": response["AuthenticationResult"]}

        except ClientError as err:
            LOGGER.error(
                "Couldn't start sign in for %s. Here's why: %s: %s",
                user_email,
                err.response["Error"]["Code"],
                err.response["Error"]["Message"],
            )
            raise

        return {"status": "UNKNOWN", "raw": response}

    def get_mfa_secret(self, session):
        """
        Gets a token that can be used to associate an MFA application with the user.

        :param session: Session information returned from a previous call to initiate
                        authentication.
        :return: A dict with the MFA SecretCode and updated Session.
        """
        try:
            response = self.cognito_idp_client.associate_software_token(Session=session)
            # LOGGER.info(f"MFA RESPONSE {response}")
        except ClientError as err:
            LOGGER.error(
                "Couldn't get MFA secret. Here's why: %s: %s",
                err.response["Error"]["Code"],
                err.response["Error"]["Message"],
            )
            raise
        else:
            response.pop("ResponseMetadata", None)
            return {
                "SecretCode": response["SecretCode"],
                "Session": response[
                    "Session"
                ],  # IMPORTANT: Updated session must be reused in verify
            }

    def verify_mfa(self, session, user_code):
        """
        Verify a new MFA application that is associated with a user.

        :param session: Session information returned from a previous call to initiate
                        authentication.
        :param user_code: A code generated by the associated MFA application.
        :return: Status that indicates whether the MFA application is verified.
        """
        try:
            response = self.cognito_idp_client.verify_software_token(
                Session=session, UserCode=user_code, FriendlyDeviceName="MyDevice"
            )
        except ClientError as err:
            LOGGER.error(
                "Couldn't verify MFA. Here's why: %s: %s",
                err.response["Error"]["Code"],
                err.response["Error"]["Message"],
            )
            raise
        else:
            response.pop("ResponseMetadata", None)
            return response

    def respond_to_mfa_challenge(
        self, user_name, session, mfa_code, challenge_name, new_password=None
    ):
        try:
            challenge_responses = {
                "USERNAME": user_name,
            }

            if self.client_secret is not None:
                challenge_responses["SECRET_HASH"] = self._secret_hash(user_name)

            # Handle challenge types
            if challenge_name == "SMS_MFA":
                challenge_responses["SMS_MFA_CODE"] = mfa_code

            elif challenge_name == "SOFTWARE_TOKEN_MFA":
                challenge_responses["SOFTWARE_TOKEN_MFA_CODE"] = mfa_code

            elif challenge_name == "EMAIL_OTP":
                challenge_responses["EMAIL_OTP_CODE"] = mfa_code

            elif challenge_name == "CUSTOM_CHALLENGE":
                challenge_responses["ANSWER"] = mfa_code

            elif challenge_name == "NEW_PASSWORD_REQUIRED":
                if not new_password:
                    raise ValueError("Missing new password for NEW_PASSWORD_REQUIRED challenge")
                challenge_responses["NEW_PASSWORD"] = new_password
                if mfa_code:
                    challenge_responses["SMS_MFA_CODE"] = mfa_code

            else:
                raise ValueError(f"Unsupported challenge type: {challenge_name}")

            kwargs = {
                "ClientId": self.client_id,
                "ChallengeName": challenge_name,
                "Session": session,
                "ChallengeResponses": challenge_responses,
            }

            # Use admin_respond_to_auth_challenge *only if* using admin flow
            response = self.cognito_idp_client.respond_to_auth_challenge(**kwargs)

            return response.get("AuthenticationResult")

        except ClientError as err:
            LOGGER.error(
                "Couldn't respond to MFA challenge for %s. Here's why: %s: %s",
                user_name,
                err.response["Error"]["Code"],
                err.response["Error"]["Message"],
            )
            raise

    def confirm_mfa_device(
        self,
        user_name,
        device_key,
        device_group_key,
        device_password,
        access_token,
        aws_srp,
    ):
        """
        Confirms an MFA device to be tracked by Amazon Cognito. When a device is
        tracked, its key and password can be used to sign in without requiring a new
        MFA code from the MFA application.

        :param user_name: The user that is associated with the device.
        :param device_key: The key of the device, returned by Amazon Cognito.
        :param device_group_key: The group key of the device, returned by Amazon Cognito.
        :param device_password: The password that is associated with the device.
        :param access_token: The user's access token.
        :param aws_srp: A class that helps with Secure Remote Password (SRP)
                        calculations. The scenario associated with this example uses
                        the warrant package.
        :return: True when the user must confirm the device. Otherwise, False. When
                    False, the device is automatically confirmed and tracked.
        """
        srp_helper = aws_srp.AWSSRP(
            username=user_name,
            password=device_password,
            pool_id="_",
            client_id=self.client_id,
            client_secret=None,
            client=self.cognito_idp_client,
        )
        device_and_pw = f"{device_group_key}{device_key}:{device_password}"
        device_and_pw_hash = aws_srp.hash_sha256(device_and_pw.encode("utf-8"))
        salt = aws_srp.pad_hex(aws_srp.get_random(16))
        x_value = aws_srp.hex_to_long(aws_srp.hex_hash(salt + device_and_pw_hash))
        verifier = aws_srp.pad_hex(pow(srp_helper.val_g, x_value, srp_helper.big_n))
        device_secret_verifier_config = {
            "PasswordVerifier": base64.standard_b64encode(bytearray.fromhex(verifier)).decode(
                "utf-8"
            ),
            "Salt": base64.standard_b64encode(bytearray.fromhex(salt)).decode("utf-8"),
        }
        try:
            response = self.cognito_idp_client.confirm_device(
                AccessToken=access_token,
                DeviceKey=device_key,
                DeviceSecretVerifierConfig=device_secret_verifier_config,
            )
            user_confirm = response["UserConfirmationNecessary"]
        except ClientError as err:
            LOGGER.error(
                "Couldn't confirm mfa device %s. Here's why: %s: %s",
                device_key,
                err.response["Error"]["Code"],
                err.response["Error"]["Message"],
            )
            raise
        else:
            return user_confirm

    def sign_in_with_tracked_device(
        self,
        user_name,
        password,
        device_key,
        device_group_key,
        device_password,
        aws_srp,
    ):
        """
        Signs in to Amazon Cognito as a user who has a tracked device. Signing in
        with a tracked device lets a user sign in without entering a new MFA code.

        Signing in with a tracked device requires that the client respond to the SRP
        protocol. The scenario associated with this example uses the warrant package
        to help with SRP calculations.

        For more information on SRP, see https://en.wikipedia.org/wiki/Secure_Remote_Password_protocol.

        :param user_name: The user that is associated with the device.
        :param password: The user's password.
        :param device_key: The key of a tracked device.
        :param device_group_key: The group key of a tracked device.
        :param device_password: The password that is associated with the device.
        :param aws_srp: A class that helps with SRP calculations. The scenario
                        associated with this example uses the warrant package.
        :return: The result of the authentication. When successful, this contains an
                    access token for the user.
        """
        try:
            srp_helper = aws_srp.AWSSRP(
                username=user_name,
                password=device_password,
                pool_id="_",
                client_id=self.client_id,
                client_secret=None,
                client=self.cognito_idp_client,
            )

            response_init = self.cognito_idp_client.initiate_auth(
                ClientId=self.client_id,
                AuthFlow="USER_PASSWORD_AUTH",
                AuthParameters={
                    "USERNAME": user_name,
                    "PASSWORD": password,
                    "DEVICE_KEY": device_key,
                },
            )
            if response_init["ChallengeName"] != "DEVICE_SRP_AUTH":
                raise RuntimeError(
                    f"Expected DEVICE_SRP_AUTH challenge but got {response_init['ChallengeName']}."
                )

            auth_params = srp_helper.get_auth_params()
            auth_params["DEVICE_KEY"] = device_key
            response_auth = self.cognito_idp_client.respond_to_auth_challenge(
                ClientId=self.client_id,
                ChallengeName="DEVICE_SRP_AUTH",
                ChallengeResponses=auth_params,
            )
            if response_auth["ChallengeName"] != "DEVICE_PASSWORD_VERIFIER":
                raise RuntimeError(
                    f"Expected DEVICE_PASSWORD_VERIFIER challenge but got "
                    f"{response_init['ChallengeName']}."
                )

            challenge_params = response_auth["ChallengeParameters"]
            challenge_params["USER_ID_FOR_SRP"] = device_group_key + device_key
            cr = srp_helper.process_challenge(challenge_params, {"USERNAME": user_name})
            cr["USERNAME"] = user_name
            cr["DEVICE_KEY"] = device_key
            response_verifier = self.cognito_idp_client.respond_to_auth_challenge(
                ClientId=self.client_id,
                ChallengeName="DEVICE_PASSWORD_VERIFIER",
                ChallengeResponses=cr,
            )
            auth_tokens = response_verifier["AuthenticationResult"]
        except ClientError as err:
            LOGGER.error(
                "Couldn't start client sign in for %s. Here's why: %s: %s",
                user_name,
                err.response["Error"]["Code"],
                err.response["Error"]["Message"],
            )
            raise
        else:
            return auth_tokens


def cognito_client():
    return CognitoIdentityProviderWrapper()
