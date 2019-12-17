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

class MovingHalfLifeHelper:
    def __init__(self, ds, hurstPeriod):
        self.__ds = ds
        self.__hurstPeriod = hurstPeriod
        self.__halfLife = None
        self.__stdDev = None
        self.__ma = None
        self.__stdDevPeriod = 50
        self.__smaPeriod = 20

    def update(self):
        if len(self.__ds) >= self.__hurstPeriod:
            values = np.asarray(self.__ds[-1 * self.__hurstPeriod:])
            self.__halfLife = int(HalfLifeUtil.getHalfLife(values))

            if self.__halfLife != None:
                self.__stdDevPeriod = self.__halfLife
                self.__smaPeriod = self.__halfLife

        if len(self.__ds) >= self.__stdDevPeriod:
            # StdDev of adjusted close values.
            self.__stdDev = StatUtil.getStd(np.asarray(self.__ds[-1 * self.__stdDevPeriod:]))
            # MA over the adjusted close values.
            self.__ma = StatUtil.getMean(np.asarray(self.__ds[-1 * self.__smaPeriod:]))

    def getHalfLife(self):
        return self.__halfLife

    def getStdDev(self):
        return self.__stdDev

    def getSma(self):
        return self.__ma
