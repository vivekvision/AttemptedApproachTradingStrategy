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

import StrategyUtil

def main(plot):

    # Load the bar feed from the CSV file
    feed = yahoofeed.Feed()

    #instrument = "n225"
    #feed.addBarsFromCSV(instrument, r".\Data\n225.csv")

    instrument = "hsi"
    feed.addBarsFromCSV(instrument, r".\Data\hsi.csv")

    calibratedStdMultiplier = 0.2
    hurstPeriod = 120

    rsiPeriod = 2
    entrySMA = 100
    exitSMA = 5
    overBoughtThreshold = 80
    overSoldThreshold = 20

    strat = StrategyUtil.ComprehensiveStrategy(feed, instrument, hurstPeriod, calibratedStdMultiplier, rsiPeriod, entrySMA, exitSMA, overBoughtThreshold, overSoldThreshold)
    sharpeRatioAnalyzer = sharpe.SharpeRatio()
    strat.attachAnalyzer(sharpeRatioAnalyzer)

    # Attach a returns analyzers to the strategy.
    returnsAnalyzer = returns.Returns()
    strat.attachAnalyzer(returnsAnalyzer)

    if plot:
        plt = plotter.StrategyPlotter(strat, True, False, True)

        plt.getOrCreateSubplot("hurst").addDataSeries("Hurst", strat.getHurst())
        plt.getOrCreateSubplot("hurst").addLine("Random", 0.5)

        # Plot the simple returns on each bar.
        plt.getOrCreateSubplot("returns").addDataSeries("Simple returns", returnsAnalyzer.getReturns())

    strat.run()
    strat.info("Final portfolio value: $%.2f" % strat.getResult())
    print("Sharpe ratio: %.2f" % sharpeRatioAnalyzer.getSharpeRatio(0.05))

    if plot:
        plt.plot()

if __name__ == "__main__":
    main(True)
