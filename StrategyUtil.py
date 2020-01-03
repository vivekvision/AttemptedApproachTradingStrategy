from pyalgotrade import strategy

from pyalgotrade.technical import ma
from pyalgotrade.technical import cross

from pyalgotrade.technical import bollinger

from pandas.plotting import register_matplotlib_converters

register_matplotlib_converters()

import MovingStatUtil
import MovingHurst

class ComprehensiveStrategy(strategy.BacktestingStrategy):
    def __init__(self, feed, instrument, hurstPeriod, stdMultiplier, bollingerBandsPeriod, bollingerBandsNoOfStd, slowSmaPeriod, fastSmaPeriod):
        strategy.BacktestingStrategy.__init__(self, feed)
        self.__instrument = instrument
        self.__hurstPeriod = hurstPeriod
        self.__calibratedStdMultiplier = stdMultiplier
        self.__position = None
        # Use adjusted close values, if available, instead of regular close values.
        if feed.barsHaveAdjClose():
            self.setUseAdjustedValues(True)
        self.__adjClosePrices = feed[instrument].getAdjCloseDataSeries()
        self.__priceDS = feed[instrument].getPriceDataSeries()
        self.__hurst = MovingHurst.HurstExponent(self.__adjClosePrices, hurstPeriod)
        self.__movingStatHelper = MovingStatUtil.MovingStatHelper(self.__adjClosePrices, hurstPeriod)

        self.__bollingerBandsPeriod = bollingerBandsPeriod
        self.__bollingerBandsNoOfStd = bollingerBandsNoOfStd
        self.__bollingerBands = bollinger.BollingerBands(self.__adjClosePrices,
                                                         self.__bollingerBandsPeriod, self.__bollingerBandsNoOfStd)

        self.__slowSma = ma.SMA(self.__priceDS, slowSmaPeriod)
        self.__fastSma = ma.SMA(self.__priceDS, fastSmaPeriod)

        self.__position = None

    def getHurst(self):
        return self.__hurst

    def getHurstValue(self):
        value = self.__hurst.getEventWindow().getValue()
        return value if value else 0.5

    def onEnterOk(self, position):
        execInfo = position.getEntryOrder().getExecutionInfo()
        self.info("Buy order at $%.2f " % (execInfo.getPrice()))

    def onEnterCanceled(self, position):
        self.__position = None

    def onExitOk(self, position):
        execInfo = position.getExitOrder().getExecutionInfo()
        self.info(" Sell order at $%.2f" % (execInfo.getPrice()))
        self.__position = None

    def onExitCanceled(self, position):
        # If the exit was canceled, re-submit it.
        position.exitMarket()


    def onBars(self, bars):
        self.__movingStatHelper.update()
        if bars.getBar(self.__instrument):
            hurst = self.getHurstValue()

            movingStdDev = self.__movingStatHelper.getMovingStdDev()
            halfLifeBasedMa = self.__movingStatHelper.getHalflifeBasedMa()

            if hurst is None or movingStdDev is None or halfLifeBasedMa is None or self.__slowSma[-1] is None or self.__fastSma[-1] is None:
                return

            bar = bars[self.__instrument]

            if hurst is not None:
                if hurst < 0.5:
                    self.meanRevAlgo(bar, halfLifeBasedMa, movingStdDev)
                elif hurst > 0.5:
                    self.momentumAlgo(bar)


    def momentumAlgo(self, bar):
        # Bollinger band based implementation
        if self.__bollingerBands.getLowerBand() is None or self.__bollingerBands.getUpperBand() is None or self.__slowSma[-1] is None or self.__fastSma[-1] is None:
            return

        if self.isMomentumRegimeBuySignal(bar):
            size = int(self.getBroker().getCash() * 0.9 / bar.getPrice())
            if size > 0:
                self.marketOrder(self.__instrument, size)
                self.info("Placing buy market order for %s shares at price %s" % (size, bar.getPrice()))
        if self.isMomentumRegimeSellSignal(bar):
            currentPosition = self.getBroker().getShares(self.__instrument)
            if currentPosition > 0:
                self.marketOrder(self.__instrument, currentPosition * -1)
                self.info("Placing sell market order for %s shares at price %s" % (currentPosition, bar.getPrice()))


    def isMomentumRegimeBuySignal(self, bar):
        return bar.getPrice() < self.__bollingerBands.getLowerBand()[-1] and cross.cross_above(self.__fastSma, self.__slowSma) > 0


    def isMomentumRegimeSellSignal(self, bar):
        return bar.getPrice() > self.__bollingerBands.getUpperBand()[-1] and cross.cross_below(self.__fastSma, self.__slowSma) > 0


    def meanRevAlgo(self, bar, halfLifeBasedMa, movingStdDev):
        # Half-life of mean reversion implementation
        if movingStdDev is None or halfLifeBasedMa is None:
            return

        if self.isMeanReversionRegimeBuySignal(halfLifeBasedMa, movingStdDev, bar):
            size = int(self.getBroker().getCash() * 0.9 / bar.getPrice())
            if size > 0:
                self.marketOrder(self.__instrument, size)
                self.info("Placing buy market order for %s shares at price %s" % (size, bar.getPrice()))

        elif self.isMeanReversionRegimeSellSignal(halfLifeBasedMa, movingStdDev, bar):
            currentPosition = self.getBroker().getShares(self.__instrument)
            if currentPosition > 0:
                self.marketOrder(self.__instrument, currentPosition * -1)
                self.info("Placing sell market order for %s shares at price %s" % (currentPosition, bar.getPrice()))


    def isMeanReversionRegimeBuySignal(self, halfLifeBasedMa, movingStdDev, bar):
        return bar.getPrice() < halfLifeBasedMa - self.__calibratedStdMultiplier * movingStdDev


    def isMeanReversionRegimeSellSignal(self, halfLifeBasedMa, movingStdDev, bar):
        return bar.getPrice() > halfLifeBasedMa - self.__calibratedStdMultiplier * movingStdDev

