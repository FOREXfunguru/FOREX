import pytest
import logging
import numpy as np

from forex.harea import HAreaList
from forex.harea import HArea
from forex.candle import Candle
from utils import DATA_DIR


@pytest.fixture
def hlist_factory():
    log = logging.getLogger('Test for hlist_factory for '
                            'returning a list of HArea objects')
    log.debug('hlist_factory')

    hlist = []
    for p in np.arange(0.660, 0.720, 0.020):
        area = HArea(price=p,
                     pips=30,
                     instrument="AUD_USD",
                     granularity="D")
        hlist.append(area)
    return hlist


def test_HAreaList_inst(hlist_factory):
    log = logging.getLogger('Instantiate a HAreaList')
    log.debug('HAreaList')

    halist = HAreaList(halist=hlist_factory)
    assert len(halist.halist) == 3


def test_onArea(hlist_factory):
    log = logging.getLogger('Test for test_onArea function')
    log.debug('test_onArea')

    halist = HAreaList(halist=hlist_factory)
    candle = {
              'time': '2018-11-18T22:00:00',
              'o': '0.68605',
              'h': '0.71258',
              'l': '0.68600',
              'c': '0.70950'
              }

    c_candle = Candle(**candle)
    (hrsel, ix) = halist.onArea(candle=c_candle)

    assert hrsel.price == 0.70
    assert ix == 2


def test_print(hlist_factory):
    '''Test 'print' function'''

    halist = HAreaList(
        halist=hlist_factory)

    res = halist.print()
    print(res)


def test_plot(hlist_factory, clO_pickled, tmp_path):
    '''Test 'plot' function'''

    halist = HAreaList(halist=hlist_factory)

    halist.plot(clO_pickled, outfile=f"{tmp_path}/AUD_USD.halist.png")


def test_from_csv():
    harea_list_object = HAreaList.from_csv(f"{DATA_DIR}/harealist_file.txt",
                                           instrument="AUD_USD",
                                           granularity="D")
    assert len(harea_list_object.halist) == 5
