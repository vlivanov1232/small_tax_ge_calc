import aiohttp


from consts import URL_CURRENCY_DATE_CUR, CURRENCIES_PARAM, DATE_PARAM
from schemas import CurrencyResponse


async def get_currency_by_date_and_cur(cur: str, date: str) -> CurrencyResponse:
    async with aiohttp.ClientSession() as session:
        params = [(CURRENCIES_PARAM, cur), (DATE_PARAM, date)]
        async with session.get(URL_CURRENCY_DATE_CUR, params=params) as response:
            response.raise_for_status()
            json_response: list[dict] = await response.json()
            currency = CurrencyResponse.from_nbg_gov(json_response)
            return currency
