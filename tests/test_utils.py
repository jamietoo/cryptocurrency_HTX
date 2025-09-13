import numpy as np
from math import isfinite

def rolling_z(x, win=5):
    x = np.asarray(x, dtype=float)
    out = np.full_like(x, np.nan)
    for i in range(len(x)):
        start = max(0, i - win + 1)
        w = x[start:i+1]
        if len(w) >= max(3, win//3):
            mu = w.mean()
            sd = w.std(ddof=0)
            out[i] = (x[i] - mu) / sd if sd > 0 else np.nan
    return out

def test_spike_registers():
    x = np.array([1,1,1,1,10,1,1], dtype=float)
    z = rolling_z(x, win=5)
    assert isfinite(z[4]) and z[4] > 3.0
