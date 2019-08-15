from oanda_api import OandaAPI
import config


oanda = OandaAPI(url=config.OANDA_API['url'],
                 instrument=pair,
                 granularity=timeframe,
                 alignmentTimezone=config.OANDA_API['alignmentTimezone'],
                 dailyAlignment=config.OANDA_API['dailyAlignment'])

oanda.run(start=self.bounce_2nd.time.isoformat(),
          end=self.bounce_1st.time.isoformat())

candle_list = oanda.fetch_candleset(vol_cutoff=0)