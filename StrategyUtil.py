from pyalgotrade import strategy
from pyalgotrade.technical import hurst
from pyalgotrade.barfeed import quandlfeed
from pyalgotrade import plotter
from pyalgotrade.stratanalyzer import sharpe
from pyalgotrade.stratanalyzer import returns
from pyalgotrade.barfeed import yahoofeed
from pyalgotrade import dataseries
from pyalgotrade.dataseries import aligned

from pyalgotrade import eventprofiler
from pyalgotrade.technical import stats
from pyalgotrade.technical import roc
from pyalgotrade.technical import ma
from pyalgotrade.technical import cross

import numpy as np
from scipy.ndimage.interpolation import shift

from pandas.plotting import register_matplotlib_converters

register_matplotlib_converters()

import MovingHalfLifeUtil
import HalfLifeUtil
import StatUtil


class HurstBasedStrategy(strategy.BacktestingStrategy):
    def __init__(self, feed, instrument, hurstPeriod):
        strategy.BacktestingStrategy.__init__(self, feed)
        self.__longWindow = 20
        self.__shortWindow = 40
        self.__instrument = instrument
        self.__position = None
        # We'll use adjusted close values instead of regular close values.
        self.setUseAdjustedValues(True)
        self.__adjClosePrices = feed[instrument].getAdjCloseDataSeries()
        self.__prices = feed[instrument].getPriceDataSeries()
        self.__hurst = hurst.HurstExponent(self.__adjClosePrices, hurstPeriod)
        self.__halfLifeHelper = MovingHalfLifeUtil.MovingHalfLifeHelper(feed[instrument].getAdjCloseDataSeries(), hurstPeriod)

        self.__longWindowMa = ma.SMA(self.__prices, self.__longWindow)
        self.__shortWindowMa = ma.SMA(self.__prices, self.__shortWindow)

    def getHurst(self):
        return self.__hurst

    def getHurstValue(self):
        value = self.__hurst.getEventWindow().getValue()
        return value if value else 0.5

    def onEnterOk(self, position):
        execInfo = position.getEntryOrder().getExecutionInfo()
        self.info("BUY at $%.2f (%.2f)" % (execInfo.getPrice(), self.getHurstValue()))

    def onEnterCanceled(self, position):
        self.__position = None

    def onExitOk(self, position):
        execInfo = position.getExitOrder().getExecutionInfo()
        self.info("SELL at $%.2f (%.2f)" % (execInfo.getPrice(), self.getHurstValue()))
        self.__position = None

    def onExitCanceled(self, position):
        # If the exit was canceled, re-submit it.
        self.__position.exitMarket()

    def sell(self, bars):
        cash = self.getBroker().getCash(False)
        price = bars[self.__instrument].getAdjClose()
        size = int((cash / price))
        if size < self.getBroker().getShares(self.__instrument):
            self.marketOrder(self.__instrument, size * -1)

    def buy(self, bars):
        cash = self.getBroker().getCash(False)
        price = bars[self.__instrument].getAdjClose()
        size = int((cash / price)*0.9)
        self.marketOrder(self.__instrument, size)

    def onBars(self, bars):
        self.__halfLifeHelper.update()
        if bars.getBar(self.__instrument):
            hurst = self.getHurstValue()
            halfLife = self.__halfLifeHelper.getHalfLife()
            stdDev = self.__halfLifeHelper.getStdDev()
            ma = self.__halfLifeHelper.getSma()
            bar = bars[self.__instrument]
            open = bar.getOpen()
            close = bar.getAdjClose()
            normalizedStd = (close - ma)/stdDev  #  normalized standard deviation = (price - moving average) / moving standard deviation
            currentPos = abs(self.getBroker().getShares(self.__instrument))
            if hurst is not None:
                if hurst < 0.5:
                    if hurst < 0.5 and normalizedStd < 0:
                        self.buy(bars)   # buy/sell  negative proportional of normalized standard deviation
                    elif hurst < 0.5 and normalizedStd> 0:
                        self.sell(bars)  # buy/sell  negative proportional of normalized standard deviation
                if hurst > 0.5:
                    if cross.cross_below(self.__shortWindowMa, self.__longWindowMa, 10) > 0 and currentPos > 0:
                        self.sell(bars)

                    if cross.cross_above(self.__longWindowMa, self.__shortWindowMa, 10) > 0:
                        self.buy(bars)
