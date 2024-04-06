import secrets

from pydantic import computed_field
from pydantic.networks import IPvAnyAddress
from pydantic_settings import BaseSettings


from typing import Optional


class Settings(BaseSettings):
    BOT_TOKEN: str

    # Heroku config
    PORT: int = 8080
    WEB_SERVER_HOST: IPvAnyAddress = "0.0.0.0"
    HEROKU_APP_DEFAULT_DOMAIN_NAME: Optional[str] = None

    # Webhook config
    USE_WEBHOOK: bool = True
    WEBHOOK_PATH: str = "/"
    WEBHOOK_SECRET: str = secrets.token_urlsafe()

    @computed_field
    def BASE_WEBHOOK_URL(self) -> str | None:
        return f"https://{self.HEROKU_APP_DEFAULT_DOMAIN_NAME}"
