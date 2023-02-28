"""
Utilities for handling authentication in the Jobbergate system.
"""
import time
from collections import namedtuple
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, cast

import httpx
from loguru import logger

from .exceptions import AuthenticationError, TokenError
from .token import Token, TokenType


LoginInformation = namedtuple(
    "LoginInformation",
    ["verification_url", "wait_interval", "device_code"],
)


@dataclass
class JobbergateAuth:
    """
    High-level class used to handle authentication in Jobbergate.

    Arguments:
        cache_directory (Path): Directory to be used for the caching tokens.
        login_domain (str): Domain used for the login.
        login_audience (str): Audience of the login.
        login_client_id (str): Client ID used for login.
        tokens (Dict[TokenType, Token]): Dictionary holding the tokens needed for authentication.

    Note:
        Consult the values above with your system administrator.

    Examples:

        The following example shows how to use the JobbergateAuth class to authenticate a request:

        >>> from pathlib import Path
        >>> import requests
        >>> from jobbergate_core import JobbergateAuth
        >>> jobbergate_auth = JobbergateAuth(
        ...     cache_directory=Path("."),
        ...     login_domain="http://keycloak.local:8080/realms/jobbergate-local",
        ...     login_audience="https://local.omnivector.solutions",
        ...     login_client_id="cli",
        ... )
        >>> jobbergate_base_url = "http://localhost:8000/jobbergate"
        >>> jobbergate_auth.acquire_tokens()
        Login Here: http://keycloak.local:8080/realms/jobbergate-local/device?user_code=LMVJ-XOLG
        >>> response = requests.get(
        ...     f"{jobbergate_base_url}/applications",
        ...     auth=jobbergate_auth # this is the important part
        )
        >>> response.raise_for_status()
        >>> print(f"response = {response.json()}")

        Notice all it takes is to pass the ``jobbergate_auth`` object to the ``auth`` parameter of
        the ``requests`` library. The same can be done with the ``httpx`` library.

        Behind the scenes, the ``jobbergate_auth`` object calls the ``acquire_tokens`` method to
        fetch the tokens from the cache directory, or refresh them if they are expired, or login
        if they are not available. See the :meth:`JobbergateAuth.acquire_tokens` method for more
        details.
    """

    cache_directory: Path
    login_domain: str
    login_audience: str
    login_client_id: str
    tokens: Dict[TokenType, Token] = field(default_factory=dict)

    def __call__(self, request):
        """
        Authenticate the request.
        """
        logger.debug("Authenticating request")

        self.acquire_tokens()
        access_token = self.check_credentials(token_type=TokenType.ACCESS)

        request.headers["Authorization"] = f"Bearer {access_token.content}"
        return request

    def acquire_tokens(self):
        """
        High-level method to acquire a valid access token.

        This method will attempt, in order:
        * Load the tokens from the cache directory
        * If the access token is unavailable or expired, refresh both tokens
          using the refresh token.
        * If the refresh token is unavailable or expired, login to fetch both tokens
        """
        logger.debug("Acquiring tokens")

        self.load_from_cache(skip_loaded=True)
        if TokenType.ACCESS in self.tokens and not self.tokens[TokenType.ACCESS].is_expired():
            return
        elif TokenType.REFRESH in self.tokens and not self.tokens[TokenType.REFRESH].is_expired():
            self.refresh_tokens()
            return
        self.login()

    def check_credentials(self, token_type: TokenType = TokenType.ACCESS) -> Token:
        """
        Check if the credentials on the provided ``token_type`` are available and not expired.

        Arguments:
            token_type (TokenType): The type of token to check (default is ``access``).

        Returns:
            Token: The token is returned for reference.

        Raises:
            AuthenticationError: If the credentials are invalid.
        """
        token = cast(Token, self.tokens.get(token_type))
        AuthenticationError.require_condition(token, f"{token_type} token was not found")
        AuthenticationError.require_condition(not token.is_expired(), f"{token_type} token has expired")

        return token

    def load_from_cache(self, skip_loaded: bool = True):
        """
        Load the tokens that are available at the cache directory.

        Arguments:
            skip_loaded (bool): If True, skip tokens that are already loaded, otherwise
                replace them with the ones from the cache.

        Note:
            This method does not check if any required token is missing nor is expired,
            for that, see :meth:`JobbergateAuth.check_credentials`.
        """
        logger.debug("Loading tokens from cache directory: {}", self.cache_directory.as_posix())

        for t in TokenType:
            if t in self.tokens and skip_loaded:
                continue
            try:
                new_token = Token.load_from_cache(self.cache_directory, label=t)
                self.tokens[t] = new_token
            except TokenError as e:
                logger.debug(f"   Error while loading {t}.token: {str(e)}")

    def save_to_cache(self):
        """
        Save the tokens to the cache directory.

        Note:
            This method will create the cache directory if it does not exist.
        """
        logger.debug(
            "Saving tokens to cache directory: {}",
            self.cache_directory.as_posix(),
        )
        self.cache_directory.mkdir(parents=True, exist_ok=True)
        for token in self.tokens.values():
            token.save_to_cache()

    def login(self):
        """
        Login to Jobbergate.
        """
        logger.debug("Preparing to login to Jobbergate")
        login_info = self._get_login_information()
        response = self._wait_for_login_confirmation(login_info)
        self._process_tokens_from_response(response)
        logger.success("Login completed")

    def _wait_for_login_confirmation(self, login_info: LoginInformation) -> httpx.Response:
        print(f"Login Here: {login_info.verification_url}")
        while True:
            response = self._get_login_confirmation(login_info)
            try:
                response.raise_for_status()
                break
            except httpx.HTTPStatusError:
                logger.debug(
                    "    Login not completed yet, waiting {} seconds",
                    login_info.wait_interval,
                )
                time.sleep(login_info.wait_interval)
        logger.debug("Preparing to login to Jobbergate")
        return response

    def _get_login_confirmation(self, login_info: LoginInformation) -> httpx.Response:

        response = httpx.post(
            f"{self.login_domain}/protocol/openid-connect/token",
            data=dict(
                grant_type="urn:ietf:params:oauth:grant-type:device_code",
                device_code=login_info.device_code,
                client_id=self.login_client_id,
            ),
        )

        return response

    def _get_login_information(self) -> LoginInformation:
        with AuthenticationError.handle_errors(
            "Unexpected error while fetching the tokens",
        ):
            response = httpx.post(
                f"{self.login_domain}/protocol/openid-connect/auth/device",
                data=dict(
                    client_id=self.login_client_id,
                    grant_type="client_credentials",
                    audience=self.login_audience,
                ),
            )
            response.raise_for_status()

        device_code_data = response.json()
        with AuthenticationError.handle_errors(
            "Error processing the request data after fetching the tokens",
        ):
            verification_url = device_code_data["verification_uri_complete"]
            wait_interval = device_code_data["interval"]
            device_code = device_code_data["device_code"]
        return LoginInformation(
            verification_url,
            wait_interval,
            device_code,
        )

    def refresh_tokens(self):
        """
        Refresh the tokens.
        """
        logger.debug("Preparing to refresh the tokens")

        refresh_token = self.check_credentials(token_type=TokenType.REFRESH)
        response = self._get_refresh_token(refresh_token)
        self._process_tokens_from_response(response)

        logger.success("Tokens refreshed successfully")

    def _get_refresh_token(self, refresh_token):
        with AuthenticationError.handle_errors(
            "Unexpected error while refreshing the tokens",
        ):
            response = httpx.post(
                f"{self.login_domain}/protocol/openid-connect/token",
                data=dict(
                    client_id=self.login_client_id,
                    audience=self.login_audience,
                    grant_type="refresh_token",
                    refresh_token=refresh_token.content,
                ),
            )
            response.raise_for_status()
        return response

    def _process_tokens_from_response(self, response):
        response_data = response.json()

        tokens_content = {t: response_data.get(f"{t}_token") for t in TokenType}
        AuthenticationError.require_condition(
            all(tokens_content.values()), "Not all tokens were included in the response"
        )
        self._update_tokens(tokens_content)
        self.save_to_cache()

    def _update_tokens(self, tokens_content: Dict[TokenType, str]):
        """
        Update the tokens with the new content.
        """

        for token_type, new_content in tokens_content.items():
            AuthenticationError.require_condition(
                token_type in TokenType,
                f"Invalid token type: {token_type}",
            )
            self.tokens[token_type] = Token(
                content=new_content,
                cache_directory=self.cache_directory,
                label=token_type,
            )
