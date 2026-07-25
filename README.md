
# ru-chat-bot

![US](https://kvaytg.ru/common/flags/us-21x16.svg) **English** | [![RU](https://kvaytg.ru/common/flags/ru-21x16.svg) Русский](README.ru.md)

![Python 3.11](https://img.shields.io/badge/Python-3.11-blue) ![PolyForm License](https://img.shields.io/badge/License-PolyForm-blue) [![Sponsor](https://img.shields.io/badge/Sponsor-%E2%9D%A4-red)](https://kvaytg.ru/donate.php?lang=en)

## 🔍 About

This is a modular deep-learning-based chatbot designed for natural language understanding and day-to-day task automation. Unlike simple script-based bots, "Neuro" (Нейро) analyzes user intent to provide contextually relevant responses.

### 🚀 Key Technologies

The project is built on a modern Natural Language Processing (NLP) stack:

* **Transformers (RuBERT):** Text vectorization is powered by the `rubert-tiny2` model, optimized via **ONNX Runtime** for lightning-fast performance even on standard CPUs.
* **NLU & Intent Classification:** A lightweight **MLP (Multi-Layer Perceptron)** classifier with **SiLU** activations and **Dropout** regularization for fast and efficient intent detection.
* **Semantic Search (DSSM):** The "Small Talk" module utilizes **FAISS** vector search to retrieve the most semantically appropriate responses for casual conversation.
* **NER (Named Entity Recognition):** Entity extraction is used for accurate weather forecasting and Wikipedia information retrieval.

### 🛠 Core Features

1. **Weather:** Real-time forecasts for any city in Russia, supporting date-specific queries.
2. **News:** Latest news headlines fetched in real-time.
3. **Wikipedia:** Instant retrieval of definitions and biographies directly within the chat.
4. **Smart Dialogue:** Ability to maintain a simple, natural conversation.
5. **Safety:** Integrated toxicity detector to filter out unwanted or harmful content.

## 📚 Usage

### 1. Environment Setup

To run the bot, create a `.env` file in the project root and add your API keys:

```env
TELEGRAM_BOT_TOKEN=YOUR_TELEGRAM_TOKEN
WEATHER_API_KEY=YOUR_OPENWEATHERMAP_KEY
# You can delete the line below to disable
PROXY_URL=http://127.0.0.1:12345
```

### 2. Launching the Bot

Example of a Telegram bot implementation using `aiogram 3.x`:

```python
import asyncio
import sys
import os
import logging
import aiohttp
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from dotenv import load_dotenv
from src.chat_bot import ChatBot

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)-25s | %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("chat-bot.log", encoding="utf-8")
    ]
)
logger = logging.getLogger(__name__)

load_dotenv()

dp = Dispatcher()


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    logger.info(f"User {message.from_user.id} started the bot")
    await message.answer("Напишите что-нибудь, чтобы начать беседу...")


@dp.message(F.text)
async def handle_text(message: types.Message, chat_bot: ChatBot):
    waiting_msg = await message.answer("Пожалуйста, подождите ⏳")
    response = await chat_bot.handle_message(message.from_user.id, message.text)
    try:
        await waiting_msg.edit_text(response)
    except Exception as e:
        logger.error(f"Ошибка отправки: {e}")


async def on_startup():
    logger.info("Бот успешно запущен и готов к работе.")


async def main():
    dp.startup.register(on_startup)
    proxy_url = os.getenv("PROXY_URL")
    async with aiohttp.ClientSession() as global_http_session:
        aiogram_session = AiohttpSession(proxy=proxy_url)
        bot = Bot(
            token=os.getenv("TELEGRAM_BOT_TOKEN"),
            session=aiogram_session,
            default=DefaultBotProperties(parse_mode="HTML", link_preview_is_disabled=True)
        )
        chat_bot = ChatBot(http_session=global_http_session)
        dp["chat_bot"] = chat_bot
        await bot.delete_webhook(drop_pending_updates=True)
        try:
            await dp.start_polling(bot)
        except Exception as e:
            logger.critical(f"Ошибка: {e}", exc_info=True)
        finally:
            await bot.session.close()
            logger.info("Сессия бота закрыта.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.warning("Бот остановлен вручную.")
```

## 📥 Installation
```bash
pip install git+https://github.com/KvaytG/ru-chat-bot.git
```

## 📝 License
Licensed under the **[PolyForm Noncommercial](LICENSE.md)** license.

This project uses open-source components. For license details see **[pyproject.toml](pyproject.toml)** and dependencies' official websites.
