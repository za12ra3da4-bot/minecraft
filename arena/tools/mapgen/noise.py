import numpy as np
from scipy import ndimage


def value_noise(size, cell, seed):
    rng = np.random.default_rng(seed)
    n = size // cell + 4
    g = rng.random((n, n))
    up = ndimage.zoom(g, cell, order=3, mode="wrap")
    return up[cell:cell + size, cell:cell + size]


def fbm(size, seed, octaves=((64, 1.0), (32, 0.5), (16, 0.25), (8, 0.12), (4, 0.06))):
    tot = np.zeros((size, size))
    norm = 0
    for i, (cell, amp) in enumerate(octaves):
        tot += (value_noise(size, cell, seed * 31 + i) - 0.5) * 2 * amp
        norm += amp
    return tot / norm


def ridge(size, seed, cell=48):
    n = value_noise(size, cell, seed)
    return 1 - np.abs(n - 0.5) * 2


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def rng(seed):
    return np.random.default_rng(seed)
