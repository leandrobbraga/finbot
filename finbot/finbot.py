import logging
import pickle
from telegram.ext import CommandHandler
from telegram.ext import Updater

from finbot.portfolio import Portfolio
from finbot.stock import Stock
from finbot.stock import StockNotFound

TOKEN: str = '<YOUR TOKEN HERE>'


def start(bot, update):
    """Welcome message."""
    bot.send_message(
        chat_id=update.message.chat_id,
        text="Welcome! \n"
        "\n"
        "Command list:\n"
        "/price *stock_code* - Verify the particular stock price.\n"
        "/buy *quantity* *stock_code* *price* - Add a stock.\n"
        "/sell *quantity* *stock_code* - Remove a quantity of the stock.\n"
        "/current - Verify your portfolio status.")


def price(bot, update, args):
    """Receive a stock code and return the price.

    Parameters:
        *args: Accept only one str argument containing the stock code (e.g. 'PETR3')

    Examples:
        /price BBAS3
        This would return the current price for BBAS3 stock"""
    stock_code = str(args[0])
    stock = Stock(stock_code)

    if stock.is_valid:
        bot.send_message(chat_id=update.message.chat_id,
                         text=f"The {stock.code} price is: R${stock.price}")
    else:
        bot.send_message(chat_id=update.message.chat_id,
                         text=f"The stock you're looking for does not exist in our database")


def buy(bot, update, args):
    """Add a new asset to the portfolio.

        Parameters:
            args: are parameters for the bought stock
                arg[0] (int): is the quantity
                arg[1] (str): is the code (e.g. 'POMO3')
                arg[2] (float): is the price
        Examples:
            /buy 100 FIIB11 225.00

            In this example you are buying 100 units of the FII named FIIB11 costing R$ 225.00 each."""
    try:
        quantity = int(args[0])
        code = str(args[1]).upper()
        price = float(args[2])

        # If we cannot find the file for this client, we create a new portfolio
        try:
            with open(f'.\\users\\{update.message.chat_id}.p', 'r+b') as data_file:
                portfolio = pickle.load(data_file)
        except FileNotFoundError:
            portfolio = Portfolio(client_id=update.message.chat_id)

        portfolio.buy_stock(code=code, quantity=quantity, price=price)

        # Save data to pickle
        with open(f'.\\users\\{portfolio.client_id}.p', 'wb') as data_file:
            pickle.dump(portfolio, data_file)

        # Send the updated portfolio
        bot.send_message(chat_id=update.message.chat_id,
                         text=f"{quantity} {code} {price:.2f} added.\n "
                              f"The new total is: "
                              f"{portfolio.stocks[code].quantity} "
                              f"{portfolio.stocks[code].code} "
                              f"{portfolio.stocks[code].avg_price:.2f}")

    # ValueError: if arg[0](quantity) could not be converted to a int or
    # arg[2] cannot be converted to float.
    # IndexError: if the args have not the at least three parameters
    except (ValueError, IndexError):
        bot.send_message(chat_id=update.message.chat_id,
                         text="We couldn't add the asset to your portfolio, ensure that you're using the following "
                              "syntax: '/buy *quantity* *stock_code* *price*'")
    # This exception is raised when the stock cannot be find in google-finance database (triggered by buy_stock method)
    except StockNotFound as error:
        bot.send_message(chat_id=update.message.chat_id, text=str(error))


def sell(bot, update, args):
    """Remove the specified quantity of the asset that the user want.

    Parameters:
        args:
            arg[0] (int): quantity of the asset to be sold
            arg[1] (str): asset code (e.g. FIIP11B)
    Examples:
        /sell 200 FIIP11B"""
    try:
        quantity = int(args[0])
        code = str(args[1]).upper()

        with open(f'.\\users\\{update.message.chat_id}.p', 'r+b') as data_file:
            portfolio = pickle.load(data_file)  # type: Portfolio
        try:
            portfolio.sell_stock(code=code, quantity=quantity)
        except (StockNotFound, ValueError) as error:
            bot.send_message(chat_id=update.message.chat_id, text=str(error))
            return

        bot.send_message(chat_id=update.message.chat_id,
                         text=f"{quantity} {code} was sold.")

        # If after sold, you still have any stock
        if code in portfolio.stocks:
            bot.send_message(
                chat_id=update.message.chat_id,
                text=f'Now you have {portfolio.stocks[code].quantity} {portfolio.stocks[code].code}')
        else:
            bot.send_message(chat_id=update.message.chat_id,
                             text=f'Now you have 0 {code}')

        with open(f'.\\users\\{portfolio.client_id}.p', 'wb') as data_file:
            pickle.dump(portfolio, data_file)

    # This check if there is really three arguments and if they have the right type
    except (ValueError, IndexError):
        bot.send_message(chat_id=update.message.chat_id,
                         text="We couldn't sell the asset from your portfolio,ensure that you're using the following "
                              "syntax: '/sell *quantity* *stock_code*'")

    # In case the client doesn't have a portfolio yet (the file doesn't exist)
    except FileNotFoundError:
        bot.send_message(chat_id=update.message.chat_id,
                         text="You don't have a portfolio yet, add an asset by using the command /buy *quantity* *code* "
                              "*price*")


def current(bot, update):
    """Show the current entire portfolio value."""
    try:
        with open(f'.\\users\\{update.message.chat_id}.p', 'rb') as data_file:
            portfolio = pickle.load(data_file)  # type: Portfolio

        # It's faster to update everything at the same time
        portfolio.update_all_stocks()

        # Use a list comprehension to build the first part of the message with
        # the list of all assets quantity, code, price and value
        msg = '\n'.join(f'{stock.quantity} {stock.code} R${stock.price:,.2f} '
                        f'{stock.change:.2%}: R${stock.value:,.2f} R${stock.avg_price * stock.quantity:,.2f}'
                        for code, stock in portfolio.stocks.items())

        # Add the trailer with the portfolio total value and change
        msg += '\n\n' + f'Your current total portfolio value is: ' \
               f'{portfolio.value:,.2f} {portfolio.change:.2%}'

        bot.send_message(chat_id=update.message.chat_id, text=msg)

    except FileNotFoundError:
        bot.send_message(chat_id=update.message.chat_id,
                         text=f"You currently don't have a portfolio in our database. You'l need to add an asset using "
                              f"/add quantity stock ")


def main():
    """Bot main function."""
    # Setup the logging system
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

    # Setup the bot updater and dispatcher
    updater = Updater(token=TOKEN)
    dispatcher = updater.dispatcher

    # Add command handler to start function
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", start))
    dispatcher.add_handler(CommandHandler("price", price, pass_args=True))
    dispatcher.add_handler(CommandHandler("buy", buy, pass_args=True))
    dispatcher.add_handler(CommandHandler("sell", sell, pass_args=True))
    dispatcher.add_handler(CommandHandler("current", current))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
