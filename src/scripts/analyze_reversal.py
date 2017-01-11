from OandaAPI import OandaAPI
from OandaAPI import Reversal
import pandas as pd
from pandas.tseries.offsets import BDay
import logging

logging.basicConfig(level=logging.INFO)
logging.info("Program started")

ic="2016-10-09 22:00:00"

r=Reversal(ic=ic,outcome=True,number_pre=3,number_post=3,instrument='AUD_USD',granularity='H12')

logging.info("Done!")
