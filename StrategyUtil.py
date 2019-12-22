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
from pyalgotrade.technical import rsi
from pyalgotrade.technical import ma
from pyalgotrade.technical import cross

from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()

import MovingStatUtil



class ComprehensiveStrategy(strategy.BacktestingStrategy):
    def __init__(self, feed, instrument, hurstPeriod, stdMultiplier, rsiPeriod, entrySMAPeriod, exitSMAPeriod, overBoughtThreshold, overSoldThreshold):
        strategy.BacktestingStrategy.__init__(self, feed)
        self.__instrument = instrument
        self.__hurstPeriod = hurstPeriod
        self.__calibratedStdMultiplier = stdMultiplier
        self.__position = None
        # Use adjusted close values instead of regular close values.
        self.setUseAdjustedValues(True)
        self.__adjClosePrices = feed[instrument].getAdjCloseDataSeries()
        self.__prices = feed[instrument].getPriceDataSeries()
        self.__hurst = hurst.HurstExponent(self.__adjClosePrices, hurstPeriod)
        self.__movingStatHelper = MovingStatUtil.MovingStatHelper(feed[instrument].getAdjCloseDataSeries(), hurstPeriod)

        self.__entrySMAPeriod = ma.SMA(self.__prices, entrySMAPeriod)
        self.__exitSMAPeriod = ma.SMA(self.__prices, exitSMAPeriod)
        self.__rsi = rsi.RSI(self.__prices, rsiPeriod)
        self.__overBoughtThreshold = overBoughtThreshold
        self.__overSoldThreshold = overSoldThreshold

        self.__longPos = None
        self.__shortPos = None

    def getHurst(self):
        return self.__hurst

    def getHurstValue(self):
        value = self.__hurst.getEventWindow().getValue()
        return value if value else 0.5

    def onEnterOk(self, position):
        execInfo = position.getEntryOrder().getExecutionInfo()
        self.info("BUY at $%.2f " % (execInfo.getPrice()))

    def onExitOk(self, position):
        execInfo = position.getExitOrder().getExecutionInfo()
        self.info("SELL at $%.2f " % (execInfo.getPrice()))

    def onEnterCanceled(self, position):
        if self.__longPos == position:
            self.__longPos = None
        elif self.__shortPos == position:
            self.__shortPos = None

    def onExitOk(self, position):
        if self.__longPos == position:
            execInfo = position.getExitOrder().getExecutionInfo()
            self.info("SELL-L at $%.2f" % (execInfo.getPrice()))
            self.__longPos = None
        elif self.__shortPos == position:
            execInfo = position.getExitOrder().getExecutionInfo()
            self.info("SELL-S at $%.2f" % (execInfo.getPrice()))
            self.__shortPos = None
        else:
            assert(False)

    def onExitCanceled(self, position):
        # If the exit was canceled, re-submit it.
        position.exitMarket()

    def sell(self, bars):
        currentPos = abs(self.getBroker().getShares(self.__instrument))
        if currentPos > 0:
            self.marketOrder(self.__instrument, currentPos * -1)
            self.info("Placing sell market order for %s shares" % currentPos)

    def buy(self, bars):
        cash = self.getBroker().getCash()
        price = bars[self.__instrument].getAdjClose()
        size = int((cash / price)*0.9)
        self.info("Placing buy market order for %s shares" % size)
        self.marketOrder(self.__instrument, size)

    def enterLongSignal(self, bar):
        return bar.getPrice() > self.__entrySMAPeriod[-1] and self.__rsi[-1] <= self.__overSoldThreshold

    def exitLongSignal(self):
        return cross.cross_above(self.__prices, self.__exitSMAPeriod) and not self.__longPos.exitActive()

    def enterShortSignal(self, bar):
        return bar.getPrice() < self.__entrySMAPeriod[-1] and self.__rsi[-1] >= self.__overBoughtThreshold

    def exitShortSignal(self):
        return cross.cross_below(self.__prices, self.__exitSMAPeriod) and not self.__shortPos.exitActive()


    def onBars(self, bars):
        self.__movingStatHelper.update()
        if bars.getBar(self.__instrument):
            hurst = self.getHurstValue()
            movingStdDev = self.__movingStatHelper.getMovingStdDev()
            ma = self.__movingStatHelper.getSma()
            bar = bars[self.__instrument]
            open = bar.getOpen()
            close = bar.getAdjClose()
            currentPos = abs(self.getBroker().getShares(self.__instrument))
            if hurst is not None:
                if hurst < 0.5:
                    if hurst < 0.5 and close < ma - self.__calibratedStdMultiplier * movingStdDev:
                        self.buy(bars)

                    elif hurst < 0.5 and close >  ma - self.__calibratedStdMultiplier * movingStdDev and currentPos > 0:
                        self.sell(bars)

                if hurst > 0.5 and self.__exitSMAPeriod[-1] is not None and self.__entrySMAPeriod[-1] is not None and self.__rsi[-1] is not None:
                    if self.__longPos is not None:
                        if self.exitLongSignal():
                            self.__longPos.exitMarket()
                    elif self.__shortPos is not None:
                        if self.exitShortSignal():
                            self.__shortPos.exitMarket()
                    else:
                        if self.enterLongSignal(bar):
                            shares = int(self.getBroker().getCash() * 0.9 / bars[self.__instrument].getPrice())
                            if shares > 0:
                                self.__longPos = self.enterLong(self.__instrument, shares, True)
                        elif self.enterShortSignal(bar):
                            shares = int(self.getBroker().getCash() * 0.9 / bars[self.__instrument].getPrice())
                            if shares > 0:
                                self.__shortPos = self.enterShort(self.__instrument, shares, True)
