from OandaAPI import OandaAPI
import logging

logging.basicConfig(level=logging.INFO)
logging.info("Program started")

#loanda=OandaAPI(url='https://api-fxtrade.oanda.com/v1/candles?',instrument='EUR_USD',granularity='H8',alignmentTimezone='Europe/London',dailyAlignment=22,start='2016-09-13T06:00:00',count=40)
oanda=OandaAPI(url='https://api-fxtrade.oanda.com/v1/candles?',instrument='EUR_USD',granularity='H8',alignmentTimezone='Europe/London',dailyAlignment=22,start='2016-10-24T22:00:00',count=1)
print oanda.print_url()

candlelist=oanda.fetch_candleset()

for c in candlelist:
    c.set_candle_features()
    c.set_candle_formation()
    print("%s %s" % (c.representation,c.time))

logging.info("Done!")
 