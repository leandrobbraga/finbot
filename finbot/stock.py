import asyncio
import json
import time

import aiohttp


def auto_updating_property(func):
    """Decorator which create a property that automaticaly updates itself."""
    def _wrapped(self: 'Stock'):
        self._update()
        return func(self)
    return property(_wrapped)


class StockNotFound(Exception):
    """Exception used when the stock doesn't exist in google-finance database."""
    pass


class Stock:
    """This class is a single stock representation. It use google-finance as it's source of information. Also, it was
     built in a lazily manner, fetching information from Google's API only when necessary.

    Parameters:
        code: Stock code (e.g. BRAS3)
        quantity: Number of stocks
        initial_price: Average value this stocks was bought
        max_cache_time: How much time in seconds stock information is cached before needing updates

    Attributes:
        code (str): Stock code (e.g. BBAS3)
        quantity (int): Number of stocks
        last_update(time.time()): Time when the price information was last updated
        avg_price (float): Average value this stock was bought"""

    def __init__(self, code: str, quantity: int = 0, initial_price: float = 0, *, max_cache_time: int = 60):
        self.code = code.upper()
        self.quantity = int(quantity)
        self.last_update: float = 0.0
        self.avg_price = float(initial_price)
        self.max_cache_time = max_cache_time

    @property
    def value(self) -> float:
        """Value of all stocks."""
        return self.quantity * self.price

    @auto_updating_property
    def price(self) -> float:
        """Stock actual price."""
        return self._price

    @auto_updating_property
    def change(self) -> float:
        """Stock change in percentage for the day."""
        return self._change

    @auto_updating_property
    def is_valid(self) -> bool:
        """Return true if the stock exist, false otherwise. Source: https://finance.google.com/"""
        return self._is_valid

    async def update_task(self) -> None:
        """Fetch asynchronously all the information from the stock.

        Note:
            Google-finance API fetches all the information at the same time (price, change, etc.). We add the following
            condition to ensure that the values are cached for at least "INFORMATION_CACHE_TIME" seconds, preventing the
            fetching of the same data when getting "price" and "change" in sequence."""
        if time.time() - self.last_update < self.max_cache_time:
            return

        url = f'https://mfinance.com.br/api/v1/stocks/{self.code}'
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as rsp:
                if rsp.status in (200,):
                    text = await rsp.text()
                    self._is_valid = True
                    # Decode the json, we remove some heading and trailing characters
                    fin_data = json.loads(text)

                    # We divide change to keep this percentage consistent with the rest of the code (i.e. each
                    # percent accounting for 0.01, e.g. 10% = 0.10)
                    self._price = float(fin_data['lastPrice'])
                    self._change = float(fin_data['change'])

                    self.last_update = time.time()
                else:
                    self._is_valid = False

    def _update(self):
        """Drive the update coroutine."""
        loop = asyncio.new_event_loop()
        loop.run_until_complete(self.update_task())
        loop.close()

    def __add__(self, other: 'Stock') -> 'Stock':
        """Add the quantity of two stock with the same code. Also, calculate the investment average price.

        Parameters:
            other: stock to be added to this object

        Raises:
            TypeError: if you didn't add two Stock objects with the same code (e.g. Stock('BBAS3') + Stock('ITSA3')
            would result in TypeError"""
        if self.code == other.code and isinstance(other, Stock):
            self.avg_price = ((self.avg_price * self.quantity) + (other.avg_price * other.quantity)) \
                             / (self.quantity + other.quantity)
            self.quantity += other.quantity
            return self
        else:
            raise TypeError(f"You're trying to add Stocks from different companies ({self.code} and {other.code})")
