import asyncio
import logging
import sys
from datetime import datetime

from aiogram import Bot, Dispatcher, F, Router, html
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
from src.consts import CURRENCIES_LIST
from src.settings import Settings

from nbg_client import get_currency_by_date_and_cur


settings = Settings()

income_router = Router()

KEYBOARD_LIST = [KeyboardButton(text=currency) for currency in CURRENCIES_LIST]


class IncomeProcess(StatesGroup):
    date = State()
    currency = State()
    amount = State()
    answer = State()


@income_router.message(Command("start"))
async def command_start(message: Message, state: FSMContext) -> None:
    await state.set_state(IncomeProcess.date)
    await message.answer(
        "Введите дату получения дохода из банковского приложения в формате ДД.ММ.ГГГГ, например 25.01.2023",
        reply_markup=ReplyKeyboardRemove(),
    )


@income_router.message(Command("cancel"))
@income_router.message(F.text.casefold() == "cancel")
async def cancel_handler(message: Message, state: FSMContext) -> None:
    current_state = await state.get_state()
    if current_state is None:
        return

    logging.info("Cancelling state %r", current_state)
    await state.clear()
    await message.answer(
        "Cancelled.",
        reply_markup=ReplyKeyboardRemove(),
    )


@income_router.message(IncomeProcess.date, F.text.regexp(r"^(0[1-9]|1\d|2\d|3[01])\.(0[1-9]|1[0-2])\.\d{4}$"))
async def process_valid_date(message: Message, state: FSMContext) -> None:
    date_object = datetime.strptime(message.text, "%d.%m.%Y").date()
    if date_object > datetime.today().date():
        await message.reply(f"Эх хотел бы я знать какой курс будет {message.text}, но не могу")
        await message.answer(
            "Введите дату получения дохода из банковского приложения в формате ДД.ММ.ГГГГ, например 25.01.2023",
            reply_markup=ReplyKeyboardRemove(),
        )
        return

    if date_object < datetime(2016, 1, 1).date():
        await message.reply("Раньше 2016 года я не могу узнать курс")
        await message.answer(
            "Введите дату получения дохода из банковского приложения в формате ДД.ММ.ГГГГ, например 25.01.2023",
            reply_markup=ReplyKeyboardRemove(),
        )
        return
    await state.update_data(date=date_object)
    await state.set_state(IncomeProcess.currency)
    await message.answer(
        "Выберите валюту из предложенных",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[KEYBOARD_LIST],
            resize_keyboard=True,
        ),
    )


@income_router.message(IncomeProcess.date)
async def process_invalid_date(message: Message) -> None:
    await message.answer(f"Вы ввели неверную дату {message.text}")
    await message.answer(
        "Введите дату получения дохода из банковского приложения в формате ДД.ММ.ГГГГ, например 25.01.2023",
        reply_markup=ReplyKeyboardRemove(),
    )


@income_router.message(IncomeProcess.currency)
async def process_currency(message: Message, state: FSMContext) -> None:
    if message.text not in CURRENCIES_LIST:
        await message.answer(
            "Выберите валюту из предложенных",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[KEYBOARD_LIST],
                resize_keyboard=True,
            ),
        )
        return
    state_dict = await state.update_data(currency=message.text)
    date_str: datetime = state_dict.get("date")
    await state.set_state(IncomeProcess.amount)
    await message.answer(
        f"Введите сумму полученную {date_str.isoformat()} в {message.text}, например 550",
        reply_markup=ReplyKeyboardRemove(),
    )


@income_router.message(IncomeProcess.amount)
async def process_amount(message: Message, state: FSMContext) -> None:
    try:
        if float(message.text) < 0:
            raise ValueError
    except ValueError:
        await message.reply("Введите целое или дробное число больше 0 без знака валют и других символов")
        return
    state_dict = await state.get_data()
    date_str: datetime = state_dict.get("date")
    currency_state = state_dict.get("currency")
    await message.reply(f"Вы ввели {message.text} {currency_state}")
    await message.answer("Запрашиваю данные в nbg.gov.ge")

    currency = await get_currency_by_date_and_cur(currency_state, date_str.isoformat())
    calculate = round(currency.currencies[0].rate * float(message.text), 4)
    await state.update_data(income=calculate)
    await state.set_state(IncomeProcess.answer)
    await message.answer(
        f"По курсу {html.italic(currency.currencies[0].code)} на {currency.currencies[0].validFromDate.date()}"
        f": {html.bold(currency.currencies[0].rate)} ваш доход составил"
    )
    await message.answer(f"{html.code(calculate)} GEL")
    await message.answer("Введите итоговый доход за прошлый отчетный период (пункт 15)")


@income_router.message(IncomeProcess.answer)
async def process_answer(message: Message, state: FSMContext) -> None:
    try:
        if float(message.text) < 0:
            raise ValueError
    except ValueError:
        await message.reply("Введите целое или дробное число больше 0 без знака валют и других символов")
        return

    state_dict = await state.get_data()
    income = state_dict.get("income")

    result_message = await message.answer(f"Итого за год (15) = {html.code(round(income + float(message.text), 4))}")
    await result_message.pin()
    await message.answer(f"За месяц (17) = {round(income, 4)}")
    await message.answer(f"Налог 1% (19) = {round(income * 0.01, 4)}")
    await message.answer("Спасибо, что воспользовались моими услугами")


async def on_startup(bot: Bot) -> None:
    await bot.set_webhook(f"{settings.BASE_WEBHOOK_URL}{settings.WEBHOOK_PATH}", secret_token=settings.WEBHOOK_SECRET)


async def main():
    bot = Bot(token=settings.BOT_TOKEN, parse_mode="HTML")
    dp = Dispatcher()
    dp.include_router(income_router)

    if not settings.USE_WEBHOOK:
        await dp.start_polling(bot)
        return

    dp.startup.register(on_startup)

    app = web.Application()

    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        secret_token=settings.WEBHOOK_SECRET,
    )
    webhook_requests_handler.register(app, path=settings.WEBHOOK_PATH)

    setup_application(app, dp, bot=bot)

    web.run_app(app, host=settings.WEB_SERVER_HOST, port=settings.PORT)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
