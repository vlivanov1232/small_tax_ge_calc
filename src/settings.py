from enum import property
from pydantic import computed_field
from pydantic_settings import BaseSettings
from pydantic.networks import HttpUrl, IPvAnyAddress
import secrets


class Settings(BaseSettings):
    BOT_TOKEN: str

    # Heroku config
    PORT: int = 8080
    WEB_SERVER_HOST: IPvAnyAddress = "0.0.0.0"
    HEROKU_APP_DEFAULT_DOMAIN_NAME: HttpUrl | None

    # Webhook config
    USE_WEBHOOK: bool = True
    WEBHOOK_PATH: str = "/"
    WEBHOOK_SECRET: str = secrets.token_urlsafe()

    @computed_field
    @property
    def BASE_WEBHOOK_URL(self):
        return f"https://{self.HEROKU_APP_DEFAULT_DOMAIN_NAME}"
