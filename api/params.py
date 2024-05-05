from dataclasses import dataclass


@dataclass
class Params:
    alignmentTimezone: int = 22
    dailyAlignment: str = "Europe/London"
    url: str = "https://api-fxtrade.oanda.com/v3/instruments/"
    roll: bool = (
        True  # If True, then extend the end date, which falls on close market,
              # to the next period for which
    )
    # the market is open. Default=False
    content_type: str = "application/json"
