import pytest
import glob
import os
import pdb

from trade_bot.trade_bot import TradeBot
from utils import DATA_DIR

@pytest.fixture
def clean_tmp():
    yield
    print("Cleanup files")
    files1 = glob.glob(f"{DATA_DIR}/out/*.png")
    files2 = glob.glob(f"{DATA_DIR}/out/*.txt")
    files = files1 + files2
    for f in files:
        os.remove(f)

@pytest.fixture
def tb_object():
    tb = TradeBot(
            pair='EUR_GBP',
            timeframe='D',
            start='2020-06-29 22:00:00',
            end='2020-07-01 22:00:00')
    return tb
