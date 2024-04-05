from datetime import datetime
from pydantic import BaseModel


class Currency(BaseModel):
    code: str
    rate: float
    date: datetime
    quantity: int
    validFromDate: datetime


class CurrencyResponse(BaseModel):
    date: datetime
    currencies: list[Currency]

    @classmethod
    def from_nbg_gov(cls, response: list[dict]):
        return cls(**response[0])
