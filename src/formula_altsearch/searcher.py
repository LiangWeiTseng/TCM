import heapq
import logging
import os
from contextlib import nullcontext
from itertools import combinations

import numpy as np
import yaml
from scipy.optimize import minimize

DEFAULT_DATAFILE = os.path.normpath(os.path.join(__file__, '..', 'database.yaml'))

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
log = logging.getLogger(__name__)

undefined = object()


def load_formula_database(file):
    try:
        # file is a path-like object
        _fh = open(file, 'r', encoding='utf-8')
    except TypeError:
        # file is a file-like object
        _fh = nullcontext(file)

    with _fh as fh:
        data = yaml.safe_load(fh)

    return _load_formula_database(data)


def _load_formula_database(data):
    rv = {}

    for _item in data:
        name = _item['name']
        key = _item['key']
        if key in rv:
            log.warning('%s 使用了重複的索引值 %s，將被忽略', repr(name), repr(key), )
            continue

        unit_dosage = _item.get('unit_dosage', 1)
        item = rv[key] = {}
        for herb, amount in _item['composition'].items():
            item[herb] = amount / unit_dosage

    return rv


def all_combinations(database, target_composition=None, excludes=None):
    excludes = set() if excludes is None else excludes

    keys = []
    for item, composition in database.items():
        if item in excludes:
            continue
        if target_composition is not None and not any(herb in target_composition for herb in composition):
            continue
        keys.append(item)

    for i in range(1, min(len(keys), 2) + 1):
        yield from combinations(keys, i)


def calculate_delta(x, target_composition, combination, database, penalty_factor):
    combined_composition = {}
    for i, formula in enumerate(combination):
        for herb, amount in database[formula].items():
            combined_composition[herb] = combined_composition.get(herb, 0) + amount * x[i]

    delta = 0
    for herb, target_amount in target_composition.items():
        combined_amount = combined_composition.get(herb, 0)
        delta += (target_amount - combined_amount) ** 2

    non_target_herbs_count = len(set(combined_composition.keys()) - set(target_composition.keys()))
    delta += penalty_factor * non_target_herbs_count

    return delta


def calculate_match(target_composition, combination, database, penalty_factor):
    initial_guess = [1 for _ in combination]
    bounds = [(0, 200) for _ in combination]
    result = minimize(calculate_delta, initial_guess, args=(target_composition, combination, database, penalty_factor), method='SLSQP', bounds=bounds)

    if not result.success:
        return [], 0, 0

    dosages = result.x
    delta = result.fun
    match_percentage = 100 - delta
    return dosages, delta, match_percentage


def _find_best_matches(database, target_composition,
                       excludes=undefined, penalty_factor=undefined):
    all_possible_combinations = all_combinations(database, target_composition, excludes)

    for combo in all_possible_combinations:
        dosages, delta, match_percentage = calculate_match(target_composition, combo, database, penalty_factor)
        log.debug('估值 %s %s: %.3f (%.2f%%)', combo, np.round(dosages, 3), delta, match_percentage)
        yield match_percentage, combo, dosages


def find_best_matches(database, target_composition, top_n=5, *args, **kwargs):
    gen = _find_best_matches(database, target_composition, *args, **kwargs)
    matches = heapq.nlargest(top_n, gen, key=lambda x: x[0])
    return matches
