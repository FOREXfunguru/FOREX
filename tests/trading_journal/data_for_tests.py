import datetime

# AUD_USD - All of them entered (mix of success/failures)
trades1 = [
    ("2016-12-28 22:00:00", "long", 0.71857, 0.70814, 0.74267, 0.72193),
    ("2017-04-11 22:00:00", "long", 0.74692, 0.73898, 0.77351, 0.75277),
    ("2017-09-11 22:00:00", "short", 0.80451, 0.81550, 0.77864, 0.80079),
    ("2018-05-03 22:00:00", "long", 0.75064, 0.74267, 0.77386, 0.75525),
]

# ["start", "pair", "timeframe", "type", "SR", "SL", "entry"]
trades_entered = [
        ("2019-04-17 22:00:00", "AUD_USD", "D", "short", 0.71600, 0.72187, 0.71433),
        ("2019-07-17 22:00:00", "AUD_USD", "D", "long", 0.69976, 0.69114, 0.70524),
        ("2019-08-25 22:00:00", "AUD_USD", "D", "long", 0.67499, 0.66530, 0.67766),
    ]


last_times = [
    datetime.datetime(2016, 2, 28, 22, 0),
    datetime.datetime(2017, 1, 9, 22, 0),
    datetime.datetime(2015, 5, 13, 21, 0),
    datetime.datetime(2017, 6, 4, 21, 0),
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
