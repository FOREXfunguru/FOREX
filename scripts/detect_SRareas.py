from oanda_api import OandaAPI
from utils import *
import config
import argparse

parser = argparse.ArgumentParser(description='Script to detect SR areas for a particular instrument/granularity')

parser.add_argument('--instrument', required=True, help='Instrument')
parser.add_argument('--granularity', required=True, help='Granularity')
parser.add_argument('--start', required=True, help='Start time to detect SR areas in isoformat')

args = parser.parse_args()

oanda = OandaAPI(url=config.OANDA_API['url'],
                 instrument=args.instrument,
                 granularity=args.granularity,
                 alignmentTimezone=config.OANDA_API['alignmentTimezone'],
                 dailyAlignment=config.OANDA_API['dailyAlignment'])

delta_period=periodToDelta(config.SRarea['period'], args.granularity)
start = args.start - delta_period # get the start datetime for this CandleList period
end = args.start

oanda.run(start=start,
          end=end,
          roll=True)

candle_list = oanda.fetch_candleset()

pivotlist = candle_list.get_pivotlist(th_up=config.SRarea['th_up'],
                                      th_down=-config.SRarea['th_down'])

def inarea_bounces(bounces, HRpips, part='closeAsk'):
    '''
    Function to identify the candles for which price is in the area defined
    by self.SR+HRpips and self.SR-HRpips

    Parameters
    ----------
    bounces: list
             Containing the initial list of candles
    HR_pips: int, Optional
             Number of pips over/below S/R used for trying to identify bounces
             Default: 200
    part: str
          Candle part used for the calculation. Default='closeAsk'

    Returns
    -------
    list with bounces that are in the area
    '''
    # get bounces in the horizontal area
    lower = substract_pips2price(self.pair, self.SR, HRpips)
    upper = add_pips2price(self.pair, self.SR, HRpips)

    in_area_list = []
    for c in bounces:
        price = getattr(c, part)
        # print("u:{0}-l:{1}|p:{2}|t:{3}".format(upper, lower, price,c.time))
        if price >= lower and price <= upper:
            in_area_list.append(c)

    return in_area_list