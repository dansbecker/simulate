import numpy as np
import pandas as pd
import pytest

from sample_datasets import *
from helpers import init_sim, v

def test_no_deps():
    sim = init_sim([v('x', '0'), v('y', '2**3')])
    assert sim.deps == {'x': set(), 'y': set()}

def test_indexed_var_ref():
    sim = init_sim([v('x', '0'), v('y', 'x[t]')])
    assert sim.deps == {'x': set(), 'y': {'x'}}

def test_nonindexed_var_ref():
    sim = init_sim([v('x', '0'), v('y', 'x')])
    assert sim.deps == {'x': set(), 'y': {'x'}}

def test_multiple_deps():
    sim = init_sim([v('x', '0'), v('y', '3'), v('z', 'x[t] + y[t]')])
    assert sim.deps == {'x': set(), 'y': set(), 'z': {'x', 'y'}}

def test_lagged_ref_creates_no_dep():
    sim = init_sim([v('x', '0', '0'), v('y', 'x[t-1]')])
    assert sim.deps == {'x': set(), 'y': set()}

def test_no_dep_on_t():
    sim = init_sim([v('x', 't')])
    assert sim.deps == {'x': set()}

def test_fn_call_arg_creates_dep():
    sim = init_sim([ v('x', '0'), v('y', 'max(x, 0)') ])
    assert sim.deps == {'x': set(), 'y': {'x'}}
