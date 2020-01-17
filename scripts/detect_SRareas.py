import argparse
import numpy as np
from Pattern.counter import Counter


parser = argparse.ArgumentParser(description='Script to detect SR areas for a particular instrument/granularity')

parser.add_argument('--instrument', required=True, help='Instrument')
parser.add_argument('--granularity', required=True, help='Granularity')
parser.add_argument('--start', required=True, help='Start time to detect SR areas in isoformat. Example: 2019-03-08 22:00:00')


args = parser.parse_args()

increment_price=0.002
# the increment of price in number of pips is double the hr_extension
for p in np.arange(0.68612, 0.75548, increment_price):
    print("Price: {0}".format(p))
    c = Counter(
        id='EUR_GBP 13AUG2019D',
        start=args.start,
        pair='EUR_GBP',
        timeframe='D',
        type='short',
        period=1000,
        SR=p,
        RR=1.5,
        png_prefix='data/tmp/test')

print("h")


