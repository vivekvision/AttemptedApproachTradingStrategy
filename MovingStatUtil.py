
# Utility to calculate moving half-life (half-life of mean reversion), moving standard deviation, moving average

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
import StatUtil
import HalfLifeUtil


class MovingStatHelper:
    def __init__(self, ds, hurstPeriod):
        self.__ds = ds
        self.__hurstPeriod = hurstPeriod
        self.__meanReversionHalfLifePeriod = None
        self.__movingStdValue = None
        self.__movingAvgValue = None
        self.__movingStdPeriod = None
        self.__movingAvgPeriod = None

    def update(self):
        if len(self.__ds) >= self.__hurstPeriod:
            values = np.asarray(self.__ds[-1 * self.__hurstPeriod:])
            self.__meanReversionHalfLifePeriod = int(HalfLifeUtil.getHalfLife(values))

            if self.__meanReversionHalfLifePeriod is not None:
                self.__movingStdPeriod = self.__meanReversionHalfLifePeriod
                self.__movingAvgPeriod = self.__meanReversionHalfLifePeriod

        if self.__movingStdPeriod is not None and self.__movingAvgPeriod is not None and len(self.__ds) >= self.__movingStdPeriod:
            # StdDev of adjusted close values.
            self.__movingStdValue = StatUtil.getStd(np.asarray(self.__ds[-1 * self.__movingStdPeriod:]))
            # MA over the adjusted close values.
            self.__movingAvgValue = StatUtil.getMean(np.asarray(self.__ds[-1 * self.__movingAvgPeriod:]))

    def getHalfLife(self):
        return self.__meanReversionHalfLifePeriod

    def getStdDev(self):
        return self.__movingStdValue

    def getSma(self):
        return self.__movingAvgValue
