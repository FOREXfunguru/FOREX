from Pattern.counter import Counter

import pytest
import pdb
import datetime
import glob
import os

@pytest.fixture
def clean_tmp():
    yield
    print("Cleanup files")
    files = glob.glob('data/IMGS/pivots/*')
    for f in files:
        os.remove(f)

@pytest.fixture
def tb_object():
    '''Returns TradeBot object'''

    t = Trade(
        id='EUR_GBP_13AUG2019D',
        start='2019-08-12 22:00:00',
        pair='EUR_GBP',
        timeframe='D',
        type='short',
        SR=0.92909,
        SL=0.93298,
        TP=0.90366,
        strat='counter_b1',
        settingf="data/settings.ini"
    )

    c = Counter(
        trade=t,
        settingf='data/settings.ini'
    )
    return c

def test_run(tb_object, clean_tmp):
    """
    Check that self.clist_period is correctly
    initialized with self.__initclist()
    """

    # check that the start datetime of clist_period
    # is correct
    assert datetime.datetime(2008, 8, 29, 21, 0) == ct_object.clist_period.clist[0].time
