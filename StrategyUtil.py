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
    def __init__(self, feed, instrument, hurstPeriod, stdMultiplier, rsiPeriod, entrySMAPeriod, exitSMAPeriod,
                 overBoughtThreshold, overSoldThreshold):
        strategy.BacktestingStrategy.__init__(self, feed)
        self.__instrument = instrument
        self.__hurstPeriod = hurstPeriod
        self.__calibratedStdMultiplier = stdMultiplier
        self.__position = None
        # Use adjusted close values instead of regular close values.
        self.setUseAdjustedValues(True)
        self.__adjClosePrices = feed[instrument].getAdjCloseDataSeries()
        self.__hurst = hurst.HurstExponent(self.__adjClosePrices, hurstPeriod)
        self.__movingStatHelper = MovingStatUtil.MovingStatHelper(feed[instrument].getAdjCloseDataSeries(), hurstPeriod)

        self.__entrySMA = ma.SMA(self.__adjClosePrices, entrySMAPeriod)
        self.__exitSMA = ma.SMA(self.__adjClosePrices, exitSMAPeriod)
        self.__rsi = rsi.RSI(self.__adjClosePrices, rsiPeriod)
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

    def onExitCanceled(self, position):
        position.exitMarket()

    def isMomentumRegimeEnterLongSignal(self, bar):
        return bar.getAdjClose() > self.__entrySMA[-1] and self.__rsi[-1] <= self.__overSoldThreshold

    def isMomentumRegimeExitLongSignal(self):
        return cross.cross_above(self.__adjClosePrices, self.__exitSMA) and not self.__longPos.exitActive()

    def isMomentumRegimeEnterShortSignal(self, bar):
        return bar.getAdjClose() < self.__entrySMA[-1] and self.__rsi[-1] >= self.__overBoughtThreshold

    def isMomentumRegimeExitShortSignal(self):
        return cross.cross_below(self.__adjClosePrices, self.__exitSMA) and not self.__shortPos.exitActive()

    def isMeanReversionRegimeEnterLongSignal(self, ma, movingStdDev, close):
        return close < ma - self.__calibratedStdMultiplier * movingStdDev

    def isMeanReversionRegimeEnterShortSignal(self, ma, movingStdDev, close):
        return close > ma - self.__calibratedStdMultiplier * movingStdDev

    def isMeanReversionRegimeExitLongSignal(self):
        return cross.cross_above(self.__adjClosePrices, self.__exitSMA) and not self.__longPos.exitActive()

    def isMeanReversionRegimeExitShortSignal(self):
        return cross.cross_below(self.__adjClosePrices, self.__exitSMA) and not self.__shortPos.exitActive()

    def onBars(self, bars):
        self.__movingStatHelper.update()
        if bars.getBar(self.__instrument):
            hurst = self.getHurstValue()
            movingStdDev = self.__movingStatHelper.getMovingStdDev()
            ma = self.__movingStatHelper.getSma()
            bar = bars[self.__instrument]
            close = bar.getAdjClose()
            if hurst is not None:
                if hurst < 0.5 and self.__exitSMA[-1] is not None:
                    if self.__longPos is not None:
                        if self.isMeanReversionRegimeExitLongSignal():
                            self.__longPos.exitMarket()
                    elif self.__shortPos is not None:
                        if self.isMeanReversionRegimeExitShortSignal():
                            self.__shortPos.exitMarket()


                    if self.isMeanReversionRegimeEnterLongSignal(ma, movingStdDev, close):
                        cash = self.getBroker().getCash() * 0.9
                        price = bars[self.__instrument].getAdjClose()
                        size = int(cash / price)
                        if size > 0:
                            self.__longPos = self.enterLong(self.__instrument, size, True)

                    elif self.isMeanReversionRegimeEnterShortSignal(ma, movingStdDev, close) and self.__shortPos is None:
                        cash = self.getBroker().getCash() * 0.9
                        price = bars[self.__instrument].getAdjClose()
                        size = int(cash / price)
                        if size > 0:
                            self.__shortPos = self.enterShort(self.__instrument, size, True)

                if hurst > 0.5 and self.__exitSMA[-1] is not None and self.__entrySMA[-1] is not None and self.__rsi[
                    -1] is not None:
                    if self.__longPos is not None:
                        if self.isMomentumRegimeExitLongSignal():
                            self.__longPos.exitMarket()
                    elif self.__shortPos is not None:
                        if self.isMomentumRegimeExitShortSignal():
                            self.__shortPos.exitMarket()
                    else:
                        if self.isMomentumRegimeEnterLongSignal(bar):
                            cash = self.getBroker().getCash() * 0.9
                            price = bars[self.__instrument].getAdjClose()
                            size = int(cash / price)
                            if size > 0:
                                self.__longPos = self.enterLong(self.__instrument, size, True)
                        elif self.isMomentumRegimeEnterShortSignal(bar) and self.__shortPos is None:
                            cash = self.getBroker().getCash() * 0.9
                            price = bars[self.__instrument].getAdjClose()
                            size = int(cash / price)
                            if size > 0:
                                self.__shortPos = self.enterShort(self.__instrument, size, True)
