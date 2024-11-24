import pytest
import datetime

from utils import calculate_profit, is_even_hour

prices = [((0.69200, 0.68750), "short", "AUD_USD", -45),
          ((0.69200, 0.68750), "long", "AUD_USD", 45),
          ((155.770, 158.245), "long", "EUR_JPY", -247.5),
          ((155.770, 158.245), "short", "EUR_JPY", 247.5)]


@pytest.mark.parametrize("bi_price,type,pair,expected", prices)
def test_calc_profit(bi_price, type, pair, expected):
    """Test function 'calc_profit'"""
    assert expected == calculate_profit(prices=bi_price, type=type, pair=pair)


datetimes = [(datetime.datetime(2015, 2, 28, 22, 0, 0), True),
             (datetime.datetime(2015, 5, 28, 9, 0, 0), False)]


@pytest.mark.parametrize("datetime,expected", datetimes)
def test_is_even_hour(datetime, expected):
    res = is_even_hour(datetime)
    assert res == expected, "Non-correct time info"
