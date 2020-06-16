import asyncio
from typing import Dict
from typing import Optional

from finbot.stock import Stock
from finbot.stock import StockNotFound


class Portfolio:
    """This class is a portfolio representation which hold assets.

    Parameters:
        client_id: Telegram id for the portfolio owner

    Attributes:
        client_id (int): Telegram id for the portfolio owner
        stocks (Dict[str, Stock]): Dict containing the owned stocks
        value (float): Value sum of all stocks in portfolio
        change (float): Percentage change of portfolio value for the day"""

    def __init__(self, client_id: int, *, stocks: Optional[Dict[str, Stock]] = None):
        if stocks is None:
            stocks = dict()

        self.client_id = client_id
        self.stocks = stocks

    @property
    def value(self) -> float:
        """Value sum of all stocks in portfolio."""
        return sum(stock.value for code, stock in self.stocks.items())

    @property
    def change(self) -> float:
        """Percentage change of portfolio value for the day."""
        return sum(stock.value * stock.change for code, stock in self.stocks.items())/self.value

    def buy_stock(self, code: str, quantity: int = 0, price: float = 0):
        """Add stocks to the portfolio.

        Parameters:
           code: stock code (e.g. BBAS3)
           quantity: number of stocks to be added
           price: price which the stock was bought

        Note:
            There are three scenarios.
            * Portfolio already has this stock - Simple add more quantity to it
            * Portfolio doesn't have this stock - Add a new stock to the portfolio
            * Stock doesn't exist in google-finance - raise a 'StockNotFound' error.

        Raises:
            StockNotFound: If stock doesn't belong to google-finance database
        """
        stock = Stock(code=code, quantity=quantity, initial_price=price)

        if stock.is_valid:
            if code in self.stocks:
                self.stocks[code] += stock
            else:
                self.stocks[code] = stock
        else:
            raise StockNotFound(f"The stock code {stock.code} couldn't be found in the database, verify if this code is"
                                f" correct")

    def sell_stock(self, code: str, quantity: int) -> None:
        """Remove a certain quantity of stocks from the portfolio.

        Parameters:
            code: stock code (e.g. 'BBAS3')
            quantity: the number of stocks to be removed

        Raises:
            ValueError: if quantity <= 0 or quantity is more than the currently possessed by the portfolio
            StockNotFound: if this portfolio doesn't have the stock to be removed

        Notes:
            if the number of stocks reaches zero, the entry is removed from the stocks dict"""
        if quantity <= 0:
            raise ValueError("It's not possible to sell less than one asset")

        if code in self.stocks:
            # Only remove the quantity if this portfolio holds enough of this stock
            if self.stocks[code].quantity >= quantity:
                self.stocks[code].quantity -= quantity
                # Delete the dict entry if the number of stocks reaches zero
                if self.stocks[code].quantity == 0:
                    del self.stocks[code]
            else:
                raise ValueError("It's not possible to sell more than you have")
        else:
            raise StockNotFound(f'There is no {code} asset in the portfolio')

    def update_all_stocks(self):
        """Updates all the stocks from the portfolio asynchronously, speeding the process up in 70%."""
        # Generate a list of tasks to be ran by the loop
        task_list = asyncio.wait([stock.update_task() for stock_code, stock in self.stocks.items()])

        # Create the loop, run and close
        loop = asyncio.new_event_loop()
        loop.run_until_complete(task_list)
        loop.close()
