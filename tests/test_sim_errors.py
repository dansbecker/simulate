"""Unit tests involving simulation inputs that should lead to user-visible
errors/warnings.
"""
import pytest

from sample_datasets import *
from helpers import run_sim as _run_sim, v, pols

# For purposes of this module specifically, we'll flip the default behaviour of
# expecting no errors when running the sim.
def run_sim(*args, **kwargs):
    kwargs.setdefault('allow_errs', True)
    return _run_sim(*args, **kwargs)


def test_sim_with_invalid_self_dep():
    user_variables = [
        {"short_name": "a", "equation": "a", "initial": 1},
    ]
    sim = run_sim(user_variables)
    sim.assert_errors_match([['a', 'equation']])


def test_handling_circular_dep_in_dataset():
    db = ASSETS_DATASET_DEF
    db['variables'] = [
        {
            "equation": "b",
            "short_name": "a",
        },
        {
            "equation": "a",
            "initial": 0,
            "short_name": "b",
        },
    ]
    sim = run_sim(datasets=[db])
    sim.assert_errors_match([
        ['EXAMPLE_LABEL.a', 'equation'],
        ['EXAMPLE_LABEL.b', 'equation'],
    ])

def test_parenthesised_expr():
    sim = run_sim([v('x', '(t*2)')], allow_errs=False)
    sim.assert_values_match('x', [0, 2, 4, 6])

def test_misparenthesised_expr():
    sim = run_sim([v('x', '(t*2))')])
    sim.assert_errors_match([ ['x', 'equation'] ])
    sim.assert_null_values('x')

def test_attribute_syntax_error():
    sim = run_sim(
            policies=pols(x=['1', 't-']),
    )
    sim.assert_errors_match([ ['x', 'equation'] ])

def test_keyword_variable_name():
    sim = run_sim([v('yield', 't')])
    sim.assert_errors_match([ ['yield', 'short_name'] ])

def test_keyword_variable_name_in_formula():
    sim = run_sim([
        v('yield', 't'),
        v('x', 'yield[t]'),
    ])
    # Should we also raise a syntax error for x's formula? Not clear.
    sim.assert_errors_include([ ['yield', 'short_name'] ])

def test_other_illegal_variable_names():
    user_variables = [
        {"short_name": "", "equation": "1",},
        {"short_name": "12x", "equation": "12",},
    ]
    pols = [
        {"policy_name": "p1", "bad name": "13"},
    ]
    sim = run_sim(user_variables, policies=pols)
    sim.assert_errors_match([
        ['', 'short_name'],
        ['12x', 'short_name'],
        ['bad name', 'short_name'],
    ])

def test_duplicate_variable_names():
    user_variables = [
        {"short_name": "x", "equation": "1",},
        {"short_name": "x", "equation": "2",},
    ]
    sim = run_sim(user_variables)
    sim.assert_errors_match([ ['x', 'short_name'] ])

def test_var_attribute_name_duplication():
    user_variables = [
        {"short_name": "x", "equation": "1",},
    ]
    pols = [
        {"policy_name": "p1", "x": "2"},
    ]
    sim = run_sim(user_variables, policies=pols)
    sim.assert_errors_match([ ['x', 'short_name'] ])

def test_misparenthesised_policy_expr():
    user_variables = [
        {"short_name": "x", "equation": "(t*2)",},
    ]
    pols = [
        {"policy_name": "p1", "y": "12"},
        {"policy_name": "p2", "y": "(t*2))"},
    ]
    sim = run_sim(user_variables, pols)
    sim.assert_errors_match([ ['y', 'equation'] ])

def test_variable_attr_circular_dep():
    user_variables = [
        {"short_name": "x", "equation": "y[t]",},
    ]
    pols = [
        {"policy_name": "p1", "y": "x[t]"},
    ]
    sim = run_sim(user_variables, pols)
    assert sim.deps == {
            'x': {'y'},
            'y': {'x'},
    }
    sim.assert_errors_match([
        ['x', 'equation'],
        ['y', 'equation'],
    ])

def test_attribute_self_dep():
    pols = [
        {"policy_name": "p1", "x": "x[t]"},
    ]
    sim = run_sim(policies=pols)
    sim.assert_errors_match([ ['x', 'equation'] ])

def test_missing_variable_dep():
    user_variables = [
        {"short_name": "x", "equation": "z[t] + 1",},
    ]
    sim = run_sim(user_variables)
    sim.assert_errors_match([ ['x', 'equation', 'No variable named z'] ])

def test_missing_lagged_variable_dep():
    user_variables = [
        {"short_name": "x", "equation": "z[t-1] + 1",},
    ]
    sim = run_sim(user_variables)
    sim.assert_errors_match([ ['x', 'equation', 'No variable named z'] ])

def test_sum_missing_column():
    db = WORKERS_DATASET_DEF.copy()
    vars = [v('x', 'sum(EXAMPLE_LABEL.not_a_column)')]
    sim = run_sim(vars, datasets=[db])
    sim.assert_errors_match([ ['x', 'equation', 'not_a_column'] ])

def test_nonexistent_dataset_label():
    db = WORKERS_DATASET_DEF.copy()
    vars = [v('x', 'sum(FAKE_DATASET.workers)')]
    sim = run_sim(vars, datasets=[db])
    sim.assert_errors_match([ ['x', 'equation', 'FAKE_DATASET'] ])

def test_initial_value_from_missing_dataset_column():
    db = WORKERS_DATASET_DEF.copy()
    # NB: This dataset doesn't have a column called "dollars"
    db['variables'] = [
            {"short_name": "x", "equation": "x[t-1] + 1", "initial": "dollars"},
    ]
    sim = run_sim(datasets=[db])
    sim.assert_errors_include([ ['EXAMPLE_LABEL.x', 'initial'] ])
    # Currently, in any case where an invalid initial value is provided, we
    # generate 2 errors: "need value before simulation" and "Initial value must be a number"
    # Should probably only show the latter? But not entirely clear.

def test_missing_model():
    sim = run_sim([v('pred', 'MY_MODEL.predict(t)')])
    sim.assert_errors_match([ ['pred', 'equation', 'MY_MODEL'] ])

def test_illegal_slicing():
    sim = run_sim([v('x', 't'), v('y', 'x[:t]')])
    sim.assert_errors_match([ ['y', 'equation'] ])

def test_missing_initial_value():
    sim = run_sim([v('x', 'x[t-1] + 1')])
    sim.assert_errors_match([ ['x', 'initial'] ])

def test_subtle_missing_initial_value():
    sim = run_sim([v('x', 'where(x[t-1], 0, 1)')], num_steps=10)
    sim.assert_errors_match([ ['x', 'initial'] ])

def test_missing_initial_value_in_other_variable_formula():
    sim = run_sim([
        v('x', 'y[t-1] + 1'),
        v('y', 'y[t-1] + 1'),
        ])
    # The calculation for both x and y will run into issues because of a missing
    # initial value for y. But the problem should be reported only once.
    sim.assert_errors_match([ ['y', 'initial'] ])

def test_not_actually_missing_initial_value():
    # Previously, this would have raised an error message about x needing an
    # initial value, because we identified that error state with looking up
    # a variable value of nan at t=0. x at 0 is nan (0/0) but it's not right
    # to say that it needs an initial value set.
    # NB: we could still create a fpos error message by defining y as x[t-1]
    # To address such situations fully, we'd need to be doing more complex 
    # dependency tracking, incorporating time offsets.
    sim = run_sim(
            [v('x', 't/0'),
             v('y', 'x[t]'),
             ],
            allow_errs=False,
    )

def test_future_dependency():
    sim = run_sim([v('x', '0'), v('y', 'x[t+1]')])
    sim.assert_errors_match([ ['y', 'equation', 'future'] ])

def test_oblique_future_dependency():
    sim = run_sim([v('x', '1'), v('y', 'x[t + x[t]]')])
    sim.assert_errors_match([ ['y', 'equation', 'future'] ])
