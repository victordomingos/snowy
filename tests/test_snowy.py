#!/usr/bin/env python3 -m pytest -s

# The shebang runs the test with stdout enabled and must be invoked from
# the repo root. In addition to this script, we use our custom doc
# generator for regression testing, because it exercises quite a bit
# of functionality to generate the images seen in the documentation.

import snowy
import numpy as np
import pytest

w, h = 1920 / 4, 1080 / 4

def smoothstep(edge0, edge1, x):
    t = np.clip((x - edge0) / (edge1 - edge0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)

def create_circle(w, h, radius=0.4, cx=0.5, cy=0.5):
    hw, hh = 0.5 / w, 0.5 / h
    dp = max(hw, hh)
    x = np.linspace(hw, 1 - hw, w)
    y = np.linspace(hh, 1 - hh, h)
    u, v = np.meshgrid(x, y, sparse=True)
    d2, r2 = (u-cx)**2 + (v-cy)**2, radius**2
    result = 1 - smoothstep(radius-dp, radius+dp, np.sqrt(d2))
    return snowy.reshape(result)

def test_minification():
    n = snowy.generate_noise(1000, 1000, frequency=5, seed=42)
    n = 0.5 + 0.5 * np.sign(n)
    a = snowy.resize(n, 100, 100)
    b = snowy.resize(n, 100, 100, snowy.MITCHELL)
    c = snowy.resize(n, 100, 100, snowy.GAUSSIAN)
    d = snowy.resize(n, 100, 100, snowy.NEAREST)
    x = [a,b,c,d] + [create_circle(100, 100)]
    snowy.show(np.hstack(x))

def test_magnification():
    i = create_circle(8, 8)
    a = snowy.resize(i, 100, 100, snowy.NEAREST)
    b = snowy.resize(i, 100, 100, snowy.TRIANGLE)
    c = snowy.resize(i, 100, 100, snowy.GAUSSIAN)
    e = snowy.resize(i, 100, 100, snowy.MITCHELL)
    d = snowy.resize(i, 100, 100, snowy.LANCZOS)
    f = snowy.resize(i, 100, 100)
    snowy.show(np.hstack([a, b, c, d, e, f]))

def test_noise_smoothness():
    noise = 0.5 + 0.5 * snowy.generate_noise(300, 150, 4, seed=42)
    grad = snowy.gradient(noise)
    grad = grad[0] + grad[1]
    grad = snowy.unitize(grad)
    snowy.show(grad)

def test_tileable():
    n = snowy.generate_noise(200, 400, frequency=4, seed=42, wrapx=True)
    n = 0.5 + 0.5 * np.sign(n) - n
    n = np.hstack([n, n])
    gold = snowy.resize(n, 200, 200)

    n = snowy.generate_noise(20, 40, frequency=4, seed=42, wrapx=True)
    n = 0.5 + 0.5 * np.sign(n) - n
    n = snowy.resize(n, 100, 200)
    bad = np.hstack([n, n])

    n = snowy.generate_noise(20, 40, frequency=4, seed=42, wrapx=True)
    n = 0.5 + 0.5 * np.sign(n) - n
    n = snowy.resize(n, 100, 200, wrapx=True)
    good = np.hstack([n, n])

    snowy.show(snowy.hstack([gold, bad, good], 2, .7))

def test_tileable_distance():
    c0 = create_circle(400, 200, 0.3)
    c1 = create_circle(400, 200, 0.08, 0.8, 0.8)
    circles = np.clip(c0 + c1, 0, 1)
    mask = circles != 0.0

    sdf = snowy.unitize(snowy.generate_sdf(mask, wrapx=True, wrapy=True))
    nx, ny = snowy.gradient(sdf)
    grad = snowy.unitize(nx + ny)
    stack2 = np.hstack([sdf, sdf, grad, grad])

    snowy.show(snowy.resize(np.vstack([stack2, stack2]), 600, 200))

    get_mask = lambda L, U: np.logical_and(sdf > L, sdf < U)
    get_contour = lambda L, U: np.where(get_mask(L, U), sdf, 0)
    sdf -= get_contour(.20, .25)
    sdf -= get_contour(.60, .65)
    sdf -= get_contour(.90, .95)

    snowy.show(snowy.resize(np.hstack([sdf, sdf, sdf, sdf]), height=300))
