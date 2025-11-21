from evaluation.eval import symetric_compare_df, df_bird_eval, bird_mod_eval
from predictors.question_prediction import Prediction
import random
from collections import defaultdict
from typing import List, Dict, Optional

def _ensure_rng(rng: Optional[random.Random]) -> random.Random:
    return rng if rng is not None else random.Random(12345)


def frequency_based_selection_tb(valid_runs: List[Prediction], rng: Optional[random.Random] = None):
        rng = _ensure_rng(rng)
        consensus = defaultdict(int)
        for i in range(len(valid_runs)):
            for j in range(i + 1, len(valid_runs)):
                if symetric_compare_df(valid_runs[i].df, valid_runs[j].df, query_category="a", question=valid_runs[i].question.text) and valid_runs[i].df is not None and valid_runs[j].df is not None:
                    consensus[i] += 1
                    consensus[j] += 1
        highest_consensus = max(consensus.values())
        best_indexes = [i for i, c in consensus.items() if c == highest_consensus]
        best_runs = [valid_runs[i] for i in best_indexes]
        return rng.choice(best_runs)
    
        
def size_based_selection_tb(valid_runs: List[Prediction], rng: Optional[random.Random] = None):
    rng = _ensure_rng(rng)
    size_dict: Dict[int, int] = defaultdict(int)
    for i in range(len(valid_runs)):
        if valid_runs[i].df is not None:
            size_dict[i] = valid_runs[i].df.size
        else:
            size_dict[i] = -1
    max_size = max(size_dict.values())
    candidates = [valid_runs[i] for i in size_dict.keys() if size_dict[i] == max_size]
    return rng.choice(candidates)

    
def density_based_selection_tb(valid_runs: List[Prediction], rng: Optional[random.Random] = None):
    rng = _ensure_rng(rng)
    density_dict: Dict[int, float] = defaultdict(float)
    for i in range(len(valid_runs)):
        current_df = valid_runs[i].df
        total_bytes = float(current_df.memory_usage(deep=True, index=False).sum())
        density_dict[i] = total_bytes / current_df.size
    max_density = max(density_dict.values())
    candidates = [valid_runs[i] for i in density_dict.keys() if density_dict[i] == max_density]
    return rng.choice(candidates)

    
def frequency_based_selection(valid_runs: List[Prediction], tb: bool = True, rng: Optional[random.Random] = None):
    rng = _ensure_rng(rng)
    consensus = defaultdict(int)
    for i in range(len(valid_runs)):
        for j in range(i + 1, len(valid_runs)):
            if symetric_compare_df(valid_runs[i].df, valid_runs[j].df, query_category="a", question=valid_runs[i].question.text) and valid_runs[i].df is not None and valid_runs[j].df is not None:
                consensus[i] += 1
                consensus[j] += 1
    if consensus == {}:
        candidates = valid_runs
    else:
        highest_consensus = max(consensus.values())
        best_indexes = [i for i, c in consensus.items() if c == highest_consensus]
        candidates = [valid_runs[i] for i in best_indexes]
    if tb:
        return rng.choice(candidates) if len(candidates) > 0 else (rng.choice(valid_runs) if len(valid_runs) > 0 else None)
    else:
        return candidates if len(candidates) > 0 else valid_runs
    
def frequency_based_selection_bird(valid_runs: List[Prediction], tb: bool = True, rng: Optional[random.Random] = None):
    rng = _ensure_rng(rng)
    consensus = defaultdict(int)
    for i in range(len(valid_runs)):
        for j in range(i + 1, len(valid_runs)):
            if df_bird_eval(valid_runs[i].df, valid_runs[j].df) and valid_runs[i].df is not None and valid_runs[j].df is not None:
                consensus[i] += 1
                consensus[j] += 1
    if consensus == {}:
        candidates = valid_runs
    else:
        highest_consensus = max(consensus.values())
        best_indexes = [i for i, c in consensus.items() if c == highest_consensus]
        candidates = [valid_runs[i] for i in best_indexes]
    if tb:
        return rng.choice(candidates) if len(candidates) > 0 else (rng.choice(valid_runs) if len(valid_runs) > 0 else None)
    else:
        return candidates if len(candidates) > 0 else valid_runs

def frequency_based_selection_bird_mod(valid_runs: List[Prediction], tb: bool = True, rng: Optional[random.Random] = None):
    rng = _ensure_rng(rng)
    consensus = defaultdict(int)
    for i in range(len(valid_runs)):
        for j in range(i + 1, len(valid_runs)):
            if bird_mod_eval(valid_runs[i].df, valid_runs[j].df) and valid_runs[i].df is not None and valid_runs[j].df is not None:
                consensus[i] += 1
                consensus[j] += 1
    if consensus == {}:
        candidates = valid_runs
    else:
        highest_consensus = max(consensus.values())
        best_indexes = [i for i, c in consensus.items() if c == highest_consensus]
        candidates = [valid_runs[i] for i in best_indexes]
    if tb:
        return rng.choice(candidates) if len(candidates) > 0 else (rng.choice(valid_runs) if len(valid_runs) > 0 else None)
    else:
        return candidates if len(candidates) > 0 else valid_runs
    
def size_based_selection(valid_runs: List[Prediction], tb: bool = True, rng: Optional[random.Random] = None):
    rng = _ensure_rng(rng)
    size_dict: Dict[int, int] = defaultdict(int)
    for i in range(len(valid_runs)):
        if valid_runs[i].df is not None:
            size_dict[i] = valid_runs[i].df.size
        else:
            size_dict[i] = -1
    max_size = max(size_dict.values())
    candidates = [valid_runs[i] for i in size_dict.keys() if size_dict[i] == max_size]
    if tb:
        return rng.choice(candidates) if len(candidates) > 0 else (rng.choice(valid_runs) if len(valid_runs) > 0 else None)
    else:
        return candidates if len(candidates) > 0 else valid_runs
    
    
def density_based_selection(valid_runs: List[Prediction], tb: bool = True, rng: Optional[random.Random] = None):
    rng = _ensure_rng(rng)
    density_dict: Dict[int, float] = defaultdict(float)
    for i in range(len(valid_runs)):
        current_df = valid_runs[i].df
        try:
            total_bytes = float(current_df.memory_usage(deep=True, index=False).sum())
            density_dict[i] = total_bytes / float(current_df.size)
        except Exception:
            density_dict[i] = -1.0
    max_density = max(density_dict.values()) if len(density_dict) > 0 else -1.0
    candidates = [valid_runs[i] for i in density_dict.keys() if density_dict[i] == max_density]
    if tb:
        return rng.choice(candidates) if len(candidates) > 0 else (rng.choice(valid_runs) if len(valid_runs) > 0 else None)
    else:
        return candidates if len(candidates) > 0 else valid_runs