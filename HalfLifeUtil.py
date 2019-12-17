
import numpy as np
from scipy.ndimage.interpolation import shift

import statsmodels.tsa.stattools as ts
import statsmodels.api as sm
from statsmodels.stats.weightstats import DescrStatsW


def getHalfLife(values):
    originalValues = np.array(values)
    shiftedValues = shift(originalValues, 1, cval=np.nan)
    shiftedValues[0] = shiftedValues[1]
    ret = originalValues - shiftedValues
    ret[0] = ret[1]
    shiftedValues2 = sm.add_constant(shiftedValues)

    model = sm.OLS(ret, shiftedValues2)
    res = model.fit()
    halflife = round(-np.log(2) / res.params[1], 0)
    return halflife