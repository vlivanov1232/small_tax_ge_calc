import secrets

from pydantic import computed_field
from pydantic.networks import IPvAnyAddress
from pydantic_settings import BaseSettings


from typing import Optional


class Settings(BaseSettings):
    BOT_TOKEN: str

    # Heroku config
    PORT: int = 3000
    WEB_SERVER_HOST: IPvAnyAddress = "0.0.0.0"
    WEBHOOK_URL: Optional[str] = None

    # Webhook config
    IS_WEBHOOK: bool = True
    WEBHOOK_PATH: str = "/"
    WEBHOOK_SECRET: str = secrets.token_urlsafe()

    @computed_field
    def BASE_WEBHOOK_URL(self) -> str | None:
        return f"https://{self.WEBHOOK_URL}"
