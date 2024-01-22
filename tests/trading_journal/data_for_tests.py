import datetime

# AUD_USD - All of them entered (mix of success/failures)
trades1 = [
    ("2016-12-28 22:00:00", "long", 0.71857, 0.70814, 0.74267, 0.72193),
    ("2017-04-11 22:00:00", "long", 0.74692, 0.73898, 0.77351, 0.75277),
    ("2017-09-11 22:00:00", "short", 0.80451, 0.81550, 0.77864, 0.80079),
    ("2018-05-03 22:00:00", "long", 0.75064, 0.74267, 0.77386, 0.75525),
]

# AUD_USD H8 2019 data- used for entered trades
trades_entered = [
    ("2019-02-11 14:00:00", "long", 0.70693, 0.69352, 0.73151, 0.70872),
    ("2019-04-17 13:00:00", "short", 0.71910, 0.72958, 0.69676, 0.71643),
    ("2019-06-18 13:00:00", "long", 0.68390, 0.67325, 0.70583, 0.68573),
    ("2019-10-22 05:00:00", "short", 0.68750, 0.69223, 0.67684, 0.68607),
]

last_times = [
    datetime.datetime(2016, 2, 28, 22, 0),
    datetime.datetime(2017, 1, 9, 22, 0),
    datetime.datetime(2015, 5, 13, 21, 0),
    datetime.datetime(2017, 6, 4, 21, 0),
]

# trades outcome used in test_UnawareTrade.py
trades_outcome = [
    ("n.a.", 86), # outcome + pips
    ("n.a.", 125.9),
    ("n.a.", 140.5),
    ("failure", -53.0)
]

start_hours = [
    (datetime.datetime(2023, 12, 9, 9, 1), datetime.datetime(2023, 12, 9, 9, 0), "H4"),
    (datetime.datetime(2023, 12, 9, 14, 37), datetime.datetime(2023, 12, 9, 13, 0), "H4"),
    (datetime.datetime(2023, 12, 9, 0, 10), datetime.datetime(2023, 12, 8, 21, 0), "H8"),
    (datetime.datetime(2023, 12, 9, 20, 0), datetime.datetime(2023, 12, 9, 9, 0), "H12"),
    (datetime.datetime(2023, 12, 9, 20, 0), datetime.datetime(2023, 12, 8, 21, 0), "D"),
    (datetime.datetime(2023, 12, 9, 23, 0), datetime.datetime(2023, 12, 9, 21, 0), "H4"),
    (datetime.datetime(2023, 7, 1, 6, 0), datetime.datetime(2023, 6, 30, 21, 0), "D")
]
