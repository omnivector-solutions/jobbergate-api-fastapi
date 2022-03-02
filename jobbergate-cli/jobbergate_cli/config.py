"""
Configuration file, sets all the necessary environment variables.
Can load configuration from a dotenv file if supplied.
"""
from pathlib import Path
from typing import Optional

from pydantic import AnyHttpUrl, BaseSettings, Field, root_validator
import urllib3

from jobbergate_cli import constants


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class Settings(BaseSettings):

    JOBBERGATE_CACHE_DIR: Path = Field(Path.home() / ".local/share/jobbergate")
    JOBBERGATE_API_ENDPOINT: AnyHttpUrl = Field("https://jobbergateapi2-staging.omnivector.solutions")

    # enable http tracing
    JOBBERGATE_DEBUG: bool = Field(False)

    SBATCH_PATH: Path = Field("/usr/bin/sbatch")
    SENTRY_DSN: Optional[str]

    # Settings for log uploads
    JOBBERGATE_AWS_ACCESS_KEY_ID: Optional[str]
    JOBBERGATE_AWS_SECRET_ACCESS_KEY: Optional[str]
    JOBBERGATE_S3_LOG_BUCKET: str = Field("jobbergate-cli-logs")

    # Computed values. Listed as Optional, but will *always* be set (or overridden) based on other values
    JOBBERGATE_APPLICATION_MODULE_PATH: Optional[Path]
    JOBBERGATE_APPLICATION_CONFIG_PATH: Optional[Path]
    JOBBERGATE_LOG_PATH: Optional[Path]
    JOBBERGATE_USER_TOKEN_DIR: Optional[Path]
    JOBBERGATE_API_ACCESS_TOKEN_PATH: Optional[Path]
    JOBBERGATE_API_REFRESH_TOKEN_PATH: Optional[Path]

    # Compatibility mode: If True, add commands as they appear in the legacy app
    JOBBERGATE_COMPATIBILITY_MODE: Optional[bool] = False

    # Auth0 config for machine-to-machine security
    AUTH0_DOMAIN: str
    AUTH0_LOGIN_DOMAIN: Optional[str]
    AUTH0_AUDIENCE: str
    AUTH0_CLIENT_ID: str
    AUTH0_CLIENT_SECRET: str
    AUTH0_MAX_POLL_TIME: int = 5 * 60  # 5 Minutes

    IDENTITY_CLAIMS_KEY: str = "https://omnivector.solutions"

    @root_validator
    def compute_extra_settings(cls, values):
        cache_dir = values["JOBBERGATE_CACHE_DIR"]
        cache_dir.mkdir(exist_ok=True, parents=True)

        values["JOBBERGATE_APPLICATION_MODULE_PATH"] = (
            cache_dir / constants.JOBBERGATE_APPLICATION_MODULE_FILE_NAME
        )
        values["JOBBERGATE_APPLICATION_CONFIG_PATH"] = (
            cache_dir / constants.JOBBERGATE_APPLICATION_CONFIG_FILE_NAME
        )

        log_dir = cache_dir / "logs"
        log_dir.mkdir(exist_ok=True, parents=True)
        values["JOBBERGATE_LOG_PATH"] = log_dir / "jobbergate-cli.log"

        token_dir = cache_dir / "token"
        token_dir.mkdir(exist_ok=True, parents=True)
        values["JOBBERGATE_USER_TOKEN_DIR"] = token_dir
        values["JOBBERGATE_API_ACCESS_TOKEN_PATH"] = token_dir / "access.token"
        values["JOBBERGATE_API_REFRESH_TOKEN_PATH"] = token_dir / "refresh.token"

        values.setdefault("AUTH0_LOGIN_DOMAIN", values["AUTH0_DOMAIN"])

        return values

    class Config:
        if constants.JOBBERGATE_DEFAULT_DOTENV_PATH.is_file():
            env_file = constants.JOBBERGATE_DEFAULT_DOTENV_PATH
        else:
            env_file = ".env"


settings = Settings()
