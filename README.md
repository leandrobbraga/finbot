# Finbot
A simple telegram bot to track stock portfolio in Bovespa.

:warning: **Google Finance API stopped working, need to change to another service.**

## Installation
First you'll need to create the bot using Telegram's [BotFather](https://t.me/botfather) to get a token. Then edit 
`finbot/finbot.py` with your bot's token and it's all set.

## Usage
The bot have a few commands:
1. **/price <STOCK_CODE>**: fetch the current price
2. **/buy <STOCK_CODE> <QUANTITY> <PRICE>**: adds a certain quantity of stocks to the user portfolio
3. **/sell <STOCK_CODE> <QUANTITY> <PRICE>**: removes a certain quantity of stock from the user portfolio
4. **/current**: summarizes the current portfolio value
