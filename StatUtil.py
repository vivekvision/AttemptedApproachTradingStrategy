
import numpy as np
from scipy.ndimage.interpolation import shift

import statsmodels.tsa.stattools as ts
import statsmodels.api as sm
from statsmodels.stats.weightstats import DescrStatsW


def getStd(returns):
    weights = np.ones_like(returns)
    stats = DescrStatsW(returns, weights=weights, ddof=0)
    return stats.std


def getMean(array):
    weights = np.ones_like(array)
    stats = DescrStatsW(array, weights=weights, ddof=0)
    return stats.mean

