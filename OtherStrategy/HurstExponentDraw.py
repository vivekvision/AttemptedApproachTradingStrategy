from pyalgotrade import strategy
from pyalgotrade.technical import hurst
from pyalgotrade.barfeed import quandlfeed
from pyalgotrade import plotter

from pyalgotrade.stratanalyzer import sharpe
from pyalgotrade.stratanalyzer import returns
from pyalgotrade.stratanalyzer import drawdown
from pyalgotrade.stratanalyzer import trades

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


class HurstStrategy(strategy.BacktestingStrategy):
    def __init__(self, feed, instrument, hurstPeriod):
        strategy.BacktestingStrategy.__init__(self, feed)
        self.__instrument = instrument
        self.__hurstPeriod = hurstPeriod
        # Use adjusted close values instead of regular close values.
        self.setUseAdjustedValues(True)
        self.__adjClosePrices = feed[instrument].getAdjCloseDataSeries()
        self.__hurst = hurst.HurstExponent(self.__adjClosePrices, self.__hurstPeriod)

    def getHurst(self):
        return self.__hurst

    def getHurstValue(self):
        value = self.__hurst.getEventWindow().getValue()
        return value if value else 0.5

    def onEnterCanceled(self, position):
        self.__position = None

    def onExitOk(self, position):
        self.__position = None

    def onExitCanceled(self, position):
        # If the exit was canceled, re-submit it.
        self.__position.exitMarket()

    def onBars(self, bars):
        pass


def main(plot):
    # Load the bar feed from the CSV file
    feed = yahoofeed.Feed()

    #instrument = "n225"
    #feed.addBarsFromCSV(instrument, r".\Data\n225.csv")

    #instrument = "hsi"
    #feed.addBarsFromCSV(instrument, r".\Data\hsi.csv")

    #instrument = "hsce"
    #feed.addBarsFromCSV(instrument, r".\Data\hsce.csv")

    #instrument = "tsec"
    #feed.addBarsFromCSV(instrument, r".\Data\tsec.csv")

    #instrument = "asx"
    #feed.addBarsFromCSV(instrument, r".\Data\asx.csv")

    #instrument = "kospi"
    #feed.addBarsFromCSV(instrument, r".\Data\kospi.csv")

    #instrument = "nifty"
    #feed.addBarsFromCSV(instrument, r".\Data\nifty.csv")

    instrument = "jkse"
    feed.addBarsFromCSV(instrument, r".\Data\jkse.csv")

    # parameters
    hurstPeriod = 100

    strat = HurstStrategy(feed, instrument, hurstPeriod)

    if plot:
        plt = plotter.StrategyPlotter(strat, True, False, True)

        plt.getOrCreateSubplot("hurst").addDataSeries("Hurst", strat.getHurst())
        plt.getOrCreateSubplot("hurst").addLine("Random", 0.5)

    strat.run()

    if plot:
        plt.plot()


if __name__ == "__main__":
    main(True)