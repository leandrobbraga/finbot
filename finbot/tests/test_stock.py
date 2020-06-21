import json

import pytest
from finbot.stock import Stock


class MockResponse:
    def __init__(self, text, status):
        self._text = text
        self.status = status

    async def text(self):
        return self._text

    async def __aexit__(self, exc_type, exc, tb):
        pass

    async def __aenter__(self):
        return self


@pytest.mark.parametrize(argnames='avg_price, expected_avg_price', argvalues=[
    (0, 9), (10, 14), (20, 19), (30, 24)
])
def test__add__(avg_price, expected_avg_price):
    stock_1 = Stock(code='ENBR3', quantity=10, initial_price=18.00)
    stock_2 = Stock(code='ENBR3', quantity=10, initial_price=avg_price)

    stock = stock_1 + stock_2

    assert stock.quantity == 20
    assert stock.avg_price == expected_avg_price


def test__add__wrong_code():
    stock_1 = Stock(code='ENBR3', quantity=10, initial_price=18.00)
    stock_2 = Stock(code='BBAS3', quantity=10, initial_price=18.00)

    with pytest.raises(TypeError):
        stock = stock_1 + stock_2


@pytest.mark.parametrize(argnames='quantity, avg_price, expected_avg_price', argvalues=[
    (10, 10, 10), (20, 10, 10), (0, 0, 0), (0, 10, 0)
])
def test__add__empty_stock(quantity, avg_price, expected_avg_price):
    stock_1 = Stock(code='ENBR3')
    stock_2 = Stock(code='ENBR3', quantity=quantity, initial_price=avg_price)

    stock = stock_1 + stock_2

    assert stock.quantity == quantity
    assert stock.avg_price == expected_avg_price


@pytest.mark.parametrize(argnames='status', argvalues=[200])
def test_update_valid_stocks(monkeypatch, status):
    data = {
        "change": 0,
        "closingPrice": 18.2,
        "eps": 2.17,
        "high": 18.37,
        "lastPrice": 18.2,
        "lastYearHigh": 23.32,
        "lastYearLow": 13.19,
        "low": 18.02,
        "marketCap": 11044677633,
        "name": "EDP Energias do Brasil SA",
        "pe": 8.4,
        "priceOpen": 18.13,
        "shares": 606850394,
        "symbol": "ENBR3",
        "volume": 4321600,
        "volumeAvg": 2530250,
        "sector": "Utilidade Pública",
        "subSector": "Energia Elétrica",
        "segment": "Energia Elétrica"
    }

    resp = MockResponse(json.dumps(data), status)

    monkeypatch.setattr('aiohttp.ClientSession.post', resp)

    stock = Stock(code='ENBR3')

    if status == 200:
        assert stock.price == 18.2
        assert stock.is_valid is True
    else:
        assert stock.is_valid is False

