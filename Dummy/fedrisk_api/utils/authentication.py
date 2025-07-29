import logging
from typing import Dict, List, Optional

import requests
from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwk, jwt
from jose.exceptions import ExpiredSignatureError, JWTError
from jose.utils import base64url_decode
from starlette.requests import Request
from starlette.status import HTTP_401_UNAUTHORIZED

from config.config import Settings

LOGGER = logging.getLogger(__name__)

JWK = Dict[str, str]
JWKS = Dict[str, List[JWK]]


class CognitoAuthorizer:
    def __init__(self):
        self.config = Settings()
        self.client_id = self.config.COGNITO_WEB_CLIENT_ID
        self.pool_id = self.config.COGNITO_USER_POOL_ID
        self.region = self.config.AWS_DEFAULT_REGION

    @staticmethod
    def _get_hmac_key(token: str, jwks: JWKS) -> Optional[JWK]:
        kid = jwt.get_unverified_header(token).get("kid")
        for key in jwks.get("keys", []):
            if key.get("kid") == kid:
                return key

    def authorize(self, token):
        hmac_key = self._get_hmac_key(token, self.jwks)

        if not hmac_key:
            raise ValueError("No public key found!")

        hmac_key1 = jwk.construct(hmac_key)

        message, encoded_signature = token.rsplit(".", 1)
        decoded_signature = base64url_decode(encoded_signature.encode())
        return hmac_key1.verify(message.encode(), decoded_signature)

    def get_user_info(self, token: str):
        user_info = jwt.get_unverified_claims(token)
        return user_info

    @property
    def jwks(self) -> JWKS:
        # TODO: make this dynamic
        jwks = requests.get(
            f"https://cognito-idp.{self.config.AWS_DEFAULT_REGION}.amazonaws.com/"
            f"{self.config.COGNITO_USER_POOL_ID}/.well-known/jwks.json"
        ).json()

        return jwks


class JWTBearer(HTTPBearer):
    def __init__(self, cognito_authorizer: CognitoAuthorizer, auto_error: bool = True):
        self.authorizer = cognito_authorizer
        super().__init__(
            auto_error=auto_error,
            scheme_name="Do Not Put your Token Here!!",
            description="This token is rarely used and most probably is not what you want to use! "
            "Most probably you want to be putting your token in the Fedrisk Token Section",
        )

    def verify_jwt(self, jwt_token: str) -> bool:
        return self.authorizer.authorize(jwt_token)

    def user_info(self, jwt_token: str):
        return self.authorizer.get_user_info(jwt_token)

    async def __call__(self, request: Request) -> Optional[str]:
        credentials: HTTPAuthorizationCredentials = await super().__call__(request)

        if not credentials:
            LOGGER.error(
                f"cognito_token_missing : "
                f"authorization key missing from request header "
                f"url:{request.url}, "
                f"path_params: {request.path_params}, "
                f"query_params: {request.query_params}, "
                f"body: {await request.body()}"
            )
            raise HTTPException(
                status_code=HTTP_401_UNAUTHORIZED,
                detail="Provide a valid token in header. Eg Authentication: Bearer xxxx",
            )

        if credentials.scheme != "Bearer":
            LOGGER.error(
                f"cognito_token_invalid_authorization_method : "
                f"url:{request.url}, "
                f"path_params: {request.path_params}, "
                f"query_params: {request.query_params}, "
                f"body: {await request.body()}"
            )
            raise HTTPException(
                status_code=HTTP_401_UNAUTHORIZED,
                detail="Wrong authentication method. Eg Authentication: Bearer xxxx",
            )

        jwt_token = credentials.credentials

        try:
            self.verify_jwt(jwt_token)
        except PermissionError as e:
            LOGGER.exception(
                f"cognito_token_not_authorized : "
                f"url:{request.url}, "
                f"path_params: {request.path_params}, "
                f"query_params: {request.query_params}, "
                f"Cognito Token : {jwt_token}"
            )
            raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Not authenticated")
        except Exception as e:
            LOGGER.exception(
                f"Cognito_token_invalid_token : "
                f"Cognito Token is Invalid "
                f"url:{request.url}, "
                f"path_params: {request.path_params}, "
                f"query_params: {request.query_params}, "
                f"Cognito Token : {jwt_token}"
            )
            raise HTTPException(
                status_code=HTTP_401_UNAUTHORIZED,
                detail="Provide a valid token in header. Eg Authentication: Bearer xxxx",
            )
        try:
            return self.user_info(jwt_token)
        except JWTError as e:
            LOGGER.exception(
                f"Cognito_token_invalid_token : "
                f"Cognito Token is Invalid error in claims "
                f"url:{request.url}, "
                f"path_params: {request.path_params}, "
                f"query_params: {request.query_params}, "
                f"Cognito Token : {jwt_token}"
            )
            raise HTTPException(
                status_code=HTTP_401_UNAUTHORIZED,
                detail="Provide a valid token in header. Eg Authentication: Bearer xxxx",
            )


cognito_auth = JWTBearer(
    CognitoAuthorizer(),
    auto_error=False,
)


class CustomJWTBearer(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super().__init__(
            auto_error=auto_error,
            scheme_name="Fedrisk Token",
            description="The token obtained by the /users/get-auth-token endpoint.  This is most probably the one you want to use!",
        )

    def user_info(self, jwt_token: str, request: Request):
        try:
            token_details = jwt.decode(
                jwt_token, Settings().FEDRISK_JWT_SECRET_KEY, algorithms=["HS256"]
            )
        except ExpiredSignatureError as e:
            LOGGER.exception(
                f"jwt_token_expired : "
                f"Token is Expired "
                f"url:{request.url}, "
                f"path_params: {request.path_params}, "
                f"query_params: {request.query_params}, "
                f"Token: {jwt_token}, "
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token is Expired. Provide a valid token in header. Eg Authentication: Bearer xxxx",
            )
        except JWTError as e:
            LOGGER.exception(
                f"jwt_token_invalid_token : "
                f"Token is invalid "
                f"url:{request.url}, "
                f"path_params: {request.path_params}, "
                f"query_params: {request.query_params}, "
                f"JWT Token: {jwt_token}, "
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Provide a valid token in header. Eg Authentication: Bearer xxxx",
            )
        try:
            cognito_token_info = jwt.get_unverified_claims(token_details["cognito_token"])
        except JWTError as e:
            LOGGER.exception(
                f"cognito_token_invalid_token : "
                f"Token is invalid "
                f"url:{request.url}, "
                f"path_params: {request.path_params}, "
                f"query_params: {request.query_params}, "
                f"Cognito Token: {token_details['cognito_token']},  "
                f"JWT Token: {jwt_token},  "
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Provide a valid token in header. Eg Authentication: Bearer xxxx",
            )
        user_details = {
            # "user_id": token_details["user_id"],
            # "email": cognito_token_info["username"],
            "user_id": token_details["user_id"],
            "email": token_details["email"],
            "tenant_id": token_details["tenant_id"],
            "exp": token_details["exp"],
            "cognito_token": token_details["cognito_token"],
        }

        return user_details

    async def __call__(self, request: Request) -> Optional[str]:
        credentials: HTTPAuthorizationCredentials = await super().__call__(request)
        if not credentials:
            LOGGER.error(
                f"jwt_token_missing : "
                f"authorization key missing from request header "
                f"url:{request.url}, "
                f"path_params: {request.path_params}, "
                f"query_params: {request.query_params}, "
                f"body: {await request.body()}"
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Provide a valid token in header. Eg Authentication: Bearer xxxx",
            )

        if not credentials.scheme == "Bearer":
            LOGGER.error(
                f"jwt_token_invalid_authorization_method : "
                f"url:{request.url}, "
                f"path_params: {request.path_params}, "
                f"query_params: {request.query_params}, "
                f"body: {await request.body()}"
            )
            raise HTTPException(
                status_code=HTTP_401_UNAUTHORIZED,
                detail="Wrong authentication method. Eg Authentication: Bearer xxxx",
            )

        jwt_token = credentials.credentials
        return self.user_info(jwt_token, request=request)


custom_auth = CustomJWTBearer(auto_error=False)
