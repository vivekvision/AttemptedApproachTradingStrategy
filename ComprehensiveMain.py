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

import StrategyUtil

def main(plot):

    # Load the bar feed from the CSV file
    feed = yahoofeed.Feed()

    #instrument = "n225"
    #feed.addBarsFromCSV(instrument, r".\Data\n225.csv")

    #instrument = "hsi"
    #feed.addBarsFromCSV(instrument, r".\Data\hsi.csv")

    instrument = "tsec"
    feed.addBarsFromCSV(instrument, r".\Data\tsec.csv")

    # parameters
    stdMultiplier = 0.2
    hurstPeriod = 100
    rsiPeriod = 2
    entrySMAPeriod = 26
    exitSMAPeriod = 9
    overBoughtThreshold = 80
    overSoldThreshold = 20

    strat = StrategyUtil.ComprehensiveStrategy(feed, instrument, hurstPeriod, stdMultiplier, rsiPeriod, entrySMAPeriod, exitSMAPeriod, overBoughtThreshold, overSoldThreshold)

    # Attach a Sharpe Ratio analyser
    sharpeRatioAnalyzer = sharpe.SharpeRatio()
    strat.attachAnalyzer(sharpeRatioAnalyzer)

    # Attach a Drawdown analyzer
    drawdownAnalyzer = drawdown.DrawDown()
    strat.attachAnalyzer(drawdownAnalyzer)

    # Attach a return analyzer
    returnsAnalyzer = returns.Returns()
    strat.attachAnalyzer(returnsAnalyzer)

    # Attach trade analyzer
    tradesAnalyzer = trades.Trades()
    strat.attachAnalyzer(tradesAnalyzer)

    if plot:
        plt = plotter.StrategyPlotter(strat, True, False, True)

        plt.getOrCreateSubplot("hurst").addDataSeries("Hurst", strat.getHurst())
        plt.getOrCreateSubplot("hurst").addLine("Random", 0.5)

        # Plot the simple returns on each bar.
        plt.getOrCreateSubplot("returns").addDataSeries("Simple returns", returnsAnalyzer.getReturns())

    strat.run()
    strat.info("Final portfolio value: $%.2f" % strat.getResult())
    print("Sharpe ratio: %.2f" % sharpeRatioAnalyzer.getSharpeRatio(0.05))
    print("Maximum Drawdown : %.2f" % drawdownAnalyzer.getMaxDrawDown())
    print("Longest Drawdown Duration : %s" % drawdownAnalyzer.getLongestDrawDownDuration())
    print("Cumulative returns: %.2f %%" % (returnsAnalyzer.getCumulativeReturns()[-1] * 100))

    print("")
    print("Total trades: %d" % (tradesAnalyzer.getCount()))
    if tradesAnalyzer.getCount() > 0:
        profits = tradesAnalyzer.getAll()
        print("Avg. profit: $%2.f" % (profits.mean()))
        print("Profits std. dev.: $%2.f" % (profits.std()))
        print("Max. profit: $%2.f" % (profits.max()))
        print("Min. profit: $%2.f" % (profits.min()))
        tradeAnalyzerAllReturns = tradesAnalyzer.getAllReturns()
        print("Avg. return: %2.f %%" % (tradeAnalyzerAllReturns.mean() * 100))
        print("Returns std. dev.: %2.f %%" % (tradeAnalyzerAllReturns.std() * 100))
        print("Max. return: %2.f %%" % (tradeAnalyzerAllReturns.max() * 100))
        print("Min. return: %2.f %%" % (tradeAnalyzerAllReturns.min() * 100))

    print("")
    print("Profitable trades: %d" % (tradesAnalyzer.getProfitableCount()))
    if tradesAnalyzer.getProfitableCount() > 0:
        profits = tradesAnalyzer.getProfits()
        print("Avg. profit: $%2.f" % (profits.mean()))
        print("Profits std. dev.: $%2.f" % (profits.std()))
        print("Max. profit: $%2.f" % (profits.max()))
        print("Min. profit: $%2.f" % (profits.min()))
        tradeAnalyzerPositiveReturns = tradesAnalyzer.getPositiveReturns()
        print("Avg. return: %2.f %%" % (tradeAnalyzerPositiveReturns.mean() * 100))
        print("Returns std. dev.: %2.f %%" % (tradeAnalyzerPositiveReturns.std() * 100))
        print("Max. return: %2.f %%" % (tradeAnalyzerPositiveReturns.max() * 100))
        print("Min. return: %2.f %%" % (tradeAnalyzerPositiveReturns.min() * 100))

    print("")
    print("Unprofitable trades: %d" % (tradesAnalyzer.getUnprofitableCount()))
    if tradesAnalyzer.getUnprofitableCount() > 0:
        losses = tradesAnalyzer.getLosses()
        print("Avg. loss: $%2.f" % (losses.mean()))
        print("Losses std. dev.: $%2.f" % (losses.std()))
        print("Max. loss: $%2.f" % (losses.min()))
        print("Min. loss: $%2.f" % (losses.max()))
        tradeAnalyzerNegativeReturns = tradesAnalyzer.getNegativeReturns()
        print("Avg. return: %2.f %%" % (tradeAnalyzerNegativeReturns.mean() * 100))
        print("Returns std. dev.: %2.f %%" % (tradeAnalyzerNegativeReturns.std() * 100))
        print("Max. return: %2.f %%" % (tradeAnalyzerNegativeReturns.max() * 100))
        print("Min. return: %2.f %%" % (tradeAnalyzerNegativeReturns.min() * 100))

    if plot:
        plt.plot()

if __name__ == "__main__":
    main(True)
