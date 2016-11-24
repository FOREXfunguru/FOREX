import requests,json


resp = requests.get('https://api-fxtrade.oanda.com/v1/candles?instrument=EUR_USD&count=2&granularity=H8&start=2015-04-21T10%3A00&count=2&dailyAlignment=22&alignmentTimezone=Europe%2FLondon&candleFormat=midpoint')

if resp.status_code != 200:
    # This means something went wrong.
    raise ('GET /tasks/ {}'.format(resp.status_code))

data = json.loads(resp.content)
print "hello"