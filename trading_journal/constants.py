# Allowed Trade class attribures
ALLOWED_ATTRBS = ["entered", "start", "end", "pair",
                  "timeframe", "outcome", "exit", "entry_time", "type",
                  "SR", "RR", "pips", "clist", "clist_tm", "strat",
                  "tot_SR", "rank_selSR"]

# 'area_unaware': exit when candles against the trade without
# considering if price is > or < than entry price
VALID_TYPES = ["area_unaware", "area_aware"]