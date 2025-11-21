"""
MLflow tracking utilities for PyDough pipeline experiments.

This module provides helper functions for MLflow experiment tracking,
including metric logging, artifact management, and metrics breakdown.
"""

import os
import json
import mlflow
import pandas as pd
import logging
import os
import json

from typing import Dict, Any, Optional
from evaluation.eval import bird_mod_eval, compare_df 

logger = logging.getLogger(__name__)


def setup_mlflow(experiment_name: str, tracking_uri: Optional[str] = None):
    """Setup MLflow tracking URI and experiment.
    
    Args:
        experiment_name: Name of the MLflow experiment
        tracking_uri: MLflow tracking server URI (defaults to env var)
    """
    # Set tracking URI
    if tracking_uri:
        mlflow.set_tracking_uri(tracking_uri)
    elif os.getenv("MLFLOW_TRACKING_URI"):
        mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI"))
    
    # Set experiment
    try:
        mlflow.set_experiment(experiment_name)
        logger.info(f"MLflow experiment set to: {experiment_name}")
    except Exception as e:
        logger.warning(f"Failed to set MLflow experiment: {e}")


def log_params_flat(params: Dict[str, Any], prefix: str = ""):
    """Log parameters to MLflow, flattening nested dictionaries.
    
    Args:
        params: Dictionary of parameters
        prefix: Prefix for parameter names
    """
    try:
        flat_params = _flatten_dict(params, prefix)
        mlflow.log_params(flat_params)
        logger.debug(f"Logged {len(flat_params)} parameters")
    except Exception as e:
        logger.error(f"Failed to log params: {e}")


def log_metrics_safe(metrics: Dict[str, float], step: Optional[int] = None):
    """Safely log metrics to MLflow.
    
    Args:
        metrics: Dictionary of metric name -> value
        step: Optional step number for time-series metrics
    """
    try:
        mlflow.log_metrics(metrics, step=step)
        logger.debug(f"Logged {len(metrics)} metrics")
    except Exception as e:
        logger.error(f"Failed to log metrics: {e}")


def log_metrics_breakdown(
    df: pd.DataFrame,
    eval_col: str = 'eval_bird',
    results_dir: Optional[str] = None
) -> Dict[str, Any]:
    """Compute and log comprehensive metrics breakdown.
    
    This function computes statistics and structures them for MLflow logging.
    
    Args:
        df: Results DataFrame
        eval_col: Evaluation column name
        results_dir: Optional directory to save JSON breakdown
        
    Returns:
        Dictionary with all computed metrics
    """
    metrics = {}
    breakdown_data = {}
    
    if eval_col not in df.columns:
        logger.warning(f"Column {eval_col} not found in DataFrame")
        return metrics
    
    # Normalize eval column
    eval_normalized = df[eval_col].astype(str).str.strip()
    
    # Overall statistics
    total_rows = len(df)
    match_count = (eval_normalized == 'Match').sum()
    nomatch_count = (eval_normalized == 'NoMatch').sum()
    error_count = (eval_normalized == 'Query error').sum()
    
    metrics[f'{eval_col}_total'] = total_rows
    metrics[f'{eval_col}_match_count'] = int(match_count)
    metrics[f'{eval_col}_nomatch_count'] = int(nomatch_count)
    metrics[f'{eval_col}_error_count'] = int(error_count)
    metrics[f'{eval_col}_match_rate'] = float(match_count / total_rows) if total_rows > 0 else 0.0
    metrics[f'{eval_col}_error_rate'] = float(error_count / total_rows) if total_rows > 0 else 0.0
    
    breakdown_data['overall'] = {
        'total': int(total_rows),
        'match': int(match_count),
        'nomatch': int(nomatch_count),
        'error': int(error_count),
        'match_rate': metrics[f'{eval_col}_match_rate'],
        'error_rate': metrics[f'{eval_col}_error_rate']
    }
    
    # Per-model statistics
    model_col = None
    for col_name in ['model', 'model_name', 'agent_name', 'run_name']:
        if col_name in df.columns:
            model_col = col_name
            break
    
    if model_col:
        model_stats = {}
        for model in df[model_col].unique():
            model_df = df[df[model_col] == model]
            model_eval = model_df[eval_col].astype(str).str.strip()
            model_total = len(model_df)
            
            model_match = (model_eval == 'Match').sum()
            model_error = (model_eval == 'Query error').sum()
            
            # Log per-model metrics
            safe_model_name = str(model).replace('/', '_').replace(' ', '_')[:100]
            metrics[f'{eval_col}_model_{safe_model_name}_match_rate'] = (
                float(model_match / model_total) if model_total > 0 else 0.0
            )
            metrics[f'{eval_col}_model_{safe_model_name}_error_rate'] = (
                float(model_error / model_total) if model_total > 0 else 0.0
            )
            
            model_stats[str(model)] = {
                'total': int(model_total),
                'match': int(model_match),
                'match_rate': float(model_match / model_total) if model_total > 0 else 0.0,
                'error': int(model_error),
                'error_rate': float(model_error / model_total) if model_total > 0 else 0.0
            }
        
        breakdown_data['per_model'] = model_stats
    
    # Per-database statistics
    if 'db_name' in df.columns:
        db_stats = {}
        for db in df['db_name'].unique():
            db_df = df[df['db_name'] == db]
            db_eval = db_df[eval_col].astype(str).str.strip()
            db_total = len(db_df)
            
            db_match = (db_eval == 'Match').sum()
            db_error = (db_eval == 'Query error').sum()
            
            db_stats[str(db)] = {
                'total': int(db_total),
                'match': int(db_match),
                'match_rate': float(db_match / db_total) if db_total > 0 else 0.0,
                'error': int(db_error),
                'error_rate': float(db_error / db_total) if db_total > 0 else 0.0
            }
        
        breakdown_data['per_database'] = db_stats
    
    # Per-question analysis (if question_index exists)
    if 'question_index' in df.columns:
        is_match = eval_normalized.eq('Match')
        per_question_matches = is_match.groupby(df['question_index']).sum().astype(int)
        
        total_questions = len(per_question_matches)
        questions_with_match = (per_question_matches >= 1).sum()
        questions_no_match = (per_question_matches == 0).sum()
        
        metrics[f'{eval_col}_total_questions'] = int(total_questions)
        metrics[f'{eval_col}_questions_with_match'] = int(questions_with_match)
        metrics[f'{eval_col}_questions_no_match'] = int(questions_no_match)
        metrics[f'{eval_col}_question_coverage'] = (
            float(questions_with_match / total_questions) if total_questions > 0 else 0.0
        )
        
        # Match distribution
        match_distribution = per_question_matches.value_counts().sort_index().to_dict()
        match_distribution = {int(k): int(v) for k, v in match_distribution.items()}
        
        breakdown_data['per_question'] = {
            'total_questions': int(total_questions),
            'questions_with_match': int(questions_with_match),
            'questions_no_match': int(questions_no_match),
            'coverage_rate': metrics[f'{eval_col}_question_coverage'],
            'match_distribution': match_distribution
        }
    
    # Log all metrics to MLflow
    log_metrics_safe(metrics)
    
    # Save breakdown as JSON artifact
    if results_dir:
        breakdown_path = os.path.join(results_dir, f'{eval_col}_breakdown.json')
        os.makedirs(results_dir, exist_ok=True)
        with open(breakdown_path, 'w') as f:
            json.dump(breakdown_data, f, indent=2)
        log_artifact_safe(breakdown_path)
    
    return breakdown_data


def extract_ensemble_config(ensemble) -> Dict[str, Any]:
    """Extract configuration from ensemble object dynamically.
    
    This function introspects the ensemble and its factories to extract
    all configuration parameters without hardcoding factory types.
    
    Args:
        ensemble: Ensemble predictor object
        
    Returns:
        Dictionary with ensemble configuration
    """
    config = {
        "ensemble_type": ensemble.ensemble_name() if hasattr(ensemble, 'ensemble_name') else type(ensemble).__name__,
        "ensemble_total_predictors": len(ensemble.predictors) if hasattr(ensemble, 'predictors') else 1,
    }
    
    # Extract factory configurations
    if hasattr(ensemble, 'factories_tries'):
        for idx, (factory, count) in enumerate(ensemble.factories_tries):
            factory_prefix = f"factory_{idx}"
            config[f"{factory_prefix}_count"] = count
            config[f"{factory_prefix}_type"] = type(factory).__name__
            
            # Extract all public attributes from factory
            factory_attrs = {k: v for k, v in factory.__dict__.items() 
                           if not k.startswith('_') and not callable(v)}
            
            for attr_name, attr_value in factory_attrs.items():
                # Only include serializable types
                if isinstance(attr_value, (str, int, float, bool, type(None))):
                    config[f"{factory_prefix}_{attr_name}"] = attr_value
                else:
                    config[f"{factory_prefix}_{attr_name}"] = str(attr_value)
    
    return config


def _flatten_dict(d: Dict, parent_key: str = '', sep: str = '_') -> Dict:
    """Flatten nested dictionary for MLflow param logging.
    
    Args:
        d: Dictionary to flatten
        parent_key: Prefix for nested keys
        sep: Separator between parent and child keys
        
    Returns:
        Flattened dictionary
    """
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        
        if isinstance(v, dict):
            items.extend(_flatten_dict(v, new_key, sep=sep).items())
        elif isinstance(v, (list, tuple)) and len(v) > 0 and isinstance(v[0], dict):
            # Handle list of dicts (e.g., ensemble configs)
            for i, item in enumerate(v):
                items.extend(_flatten_dict(item, f"{new_key}_{i}", sep=sep).items())
        else:
            # Convert to string if not a basic type
            if isinstance(v, (int, float, str, bool, type(None))):
                items.append((new_key, v))
            else:
                items.append((new_key, str(v)))
    
    return dict(items)


from pathlib import Path


def process_individuals_results(results: list, experiment_dataset: str, total_questions: int, csv_path: str):
    """
    Process individual model results from ensemble predictions and save per-model statistics.
    Tracks matches, query errors, and coverage for each model.
    """
    model_stats = {}
    question_matches = {}  # Track which questions have matches per model
    
    for result in results:
        # if prediction is None, means it failed completely, need to sum to the right predictions
        if result.prediction is None:
            continue
            
        # Process valid predictions
        for pred in result.prediction.valid_predictions:
            model_name = pred.model_name
            question_id = pred.question.question_id
            
            if model_name not in model_stats:
                model_stats[model_name] = {
                    'total': 0,
                    'match': 0,
                    'no_match': 0,
                    'query_error': 0
                }
                question_matches[model_name] = set()
            
            model_stats[model_name]['total'] += 1
            
            # Check if this prediction matches ground truth
            custom_cmp = bird_mod_eval(pred.question.ground_truth_df, pred.df)
            
            if custom_cmp:
                model_stats[model_name]['match'] += 1
                question_matches[model_name].add(question_id)
            else:
                model_stats[model_name]['no_match'] += 1
        
        # Process invalid predictions (query errors)
        for pred in result.prediction.invalid_predictions:
            model_name = pred.model_name
            
            if model_name not in model_stats:
                model_stats[model_name] = {
                    'total': 0,
                    'match': 0,
                    'no_match': 0,
                    'query_error': 0
                }
                question_matches[model_name] = set()
            
            model_stats[model_name]['total'] += 1
            model_stats[model_name]['query_error'] += 1
    
    # Calculate percentages and prepare output
    summary_data = []
    for model_name, stats in sorted(model_stats.items()):
        match_pct = (stats['match'] / stats['total'] * 100) if stats['total'] > 0 else 0
        no_match_pct = (stats['no_match'] / stats['total'] * 100) if stats['total'] > 0 else 0
        query_error_pct = (stats['query_error'] / stats['total'] * 100) if stats['total'] > 0 else 0
        coverage_pct = (len(question_matches[model_name]) / total_questions * 100) if total_questions > 0 else 0
        
        summary_data.append({
            'Model': model_name,
            'Total': stats['total'],
            'Match': stats['match'],
            'Match%': f"{match_pct:.1f}%",
            'NoMatch': stats['no_match'],
            'NoMatch%': f"{no_match_pct:.1f}%",
            'QueryError': stats['query_error'],
            'QueryError%': f"{query_error_pct:.1f}%",
            'Questions_w_Match': len(question_matches[model_name]),
            'Coverage%': f"{coverage_pct:.1f}%",
            'Total_Rows': stats['total'],
            'Total_Questions': total_questions
        })
    
    # Add model combinations if there are multiple models
    model_names = sorted(question_matches.keys())
    if len(model_names) > 1:
        from itertools import combinations
        
        # Calculate pairwise combinations
        for i in range(2, min(len(model_names) + 1, 4)):  # Up to 3-way combinations
            for combo in combinations(model_names, i):
                # Union of all matched questions across models in combination
                union_matches = set()
                combo_total = 0
                combo_match = 0
                combo_no_match = 0
                combo_query_error = 0
                
                for model in combo:
                    union_matches.update(question_matches[model])
                    combo_total += model_stats[model]['total']
                    combo_match += model_stats[model]['match']
                    combo_no_match += model_stats[model]['no_match']
                    combo_query_error += model_stats[model]['query_error']
                
                combo_name = " + ".join([m.split('/')[-1] if '/' in m else m for m in combo])
                coverage_pct = (len(union_matches) / total_questions * 100) if total_questions > 0 else 0
                match_pct = (combo_match / combo_total * 100) if combo_total > 0 else 0
                no_match_pct = (combo_no_match / combo_total * 100) if combo_total > 0 else 0
                query_error_pct = (combo_query_error / combo_total * 100) if combo_total > 0 else 0
                
                summary_data.append({
                    'Model': f"{combo_name}",
                    'Total': combo_total,
                    'Match': combo_match,
                    'Match%': f"{match_pct:.1f}%",
                    'NoMatch': combo_no_match,
                    'NoMatch%': f"{no_match_pct:.1f}%",
                    'QueryError': combo_query_error,
                    'QueryError%': f"{query_error_pct:.1f}%",
                    'Questions_w_Match': len(union_matches),
                    'Coverage%': f"{coverage_pct:.1f}%",
                    'Total_Rows': combo_total,
                    'Total_Questions': total_questions
                })
    
    # Save to CSV
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    df = pd.DataFrame(summary_data)
    df.to_csv(csv_path, index=False)
    
    # Log to MLflow if active
    if mlflow.active_run():
        for model_name, stats in model_stats.items():
            # Sanitize model name for MLflow (replace @ and other invalid chars)
            safe_model_name = model_name.replace('@', '_').replace('/', '_').replace('\\', '_')
            mlflow.log_metrics({
                f"{safe_model_name}_total": stats['total'],
                f"{safe_model_name}_match": stats['match'],
                f"{safe_model_name}_match_rate": stats['match'] / stats['total'] if stats['total'] > 0 else 0,
                f"{safe_model_name}_coverage": len(question_matches[model_name]) / total_questions if total_questions > 0 else 0,
                f"{safe_model_name}_query_error_rate": stats['query_error'] / stats['total'] if stats['total'] > 0 else 0,
            })
        
        # Log the CSV as artifact
        mlflow.log_artifact(csv_path)
    
    print(f"\nPer-Model Statistics saved to: {csv_path}")
    print(df.to_string(index=False))


def process_per_question_match_distribution(results: list, experiment_dataset: str, total_questions: int, csv_path: str, eval_method: str = "eval_custom"):
    """
    Calculate per-question match count distribution.
    Shows how many questions got 0 matches, 1 match, 2 matches, etc.
    
    Args:
        results: List of ExperimentResult objects
        experiment_dataset: Name of the dataset being evaluated
        total_questions: Total number of questions in the dataset
        csv_path: Path to save the CSV file
        eval_method: Evaluation method name ("eval_custom" or "eval_bird")
    """
    from collections import Counter
    
    # Track matches per question
    question_match_counts = {}
    
    for result in results:
        if result.prediction is None:
            continue
        
        question_id = result.prediction.question.question_id
        
        if question_id not in question_match_counts:
            question_match_counts[question_id] = 0
        
        # Count how many valid predictions match for this question
        for pred in result.prediction.valid_predictions:
            # Use appropriate comparison based on eval_method
            if eval_method == "eval_bird":
                match = bird_mod_eval(pred.question.ground_truth_df, pred.df)
            else:  # eval_custom
                match = compare_df(pred.question.ground_truth_df, pred.df, None, pred.question.text)
            
            if match:
                question_match_counts[question_id] += 1
    
    # Count distribution of match counts
    match_distribution = Counter(question_match_counts.values())
    
    # Also count questions with 0 matches (not in valid_predictions)
    questions_with_results = set(question_match_counts.keys())
    total_questions_processed = len(questions_with_results)
    questions_with_zero_matches = total_questions - total_questions_processed
    
    if questions_with_zero_matches > 0:
        match_distribution[0] = match_distribution.get(0, 0) + questions_with_zero_matches
    
    # Prepare summary data
    summary_data = []
    total_with_at_least_one = 0
    
    for match_count in sorted(match_distribution.keys()):
        num_questions = match_distribution[match_count]
        percentage = (num_questions / total_questions * 100) if total_questions > 0 else 0
        
        if match_count > 0:
            total_with_at_least_one += num_questions
        
        summary_data.append({
            'Match_Count': match_count,
            'Num_Questions': num_questions,
            'Percentage': f"{percentage:.1f}%"
        })
    
    # Add summary row
    coverage_pct = (total_with_at_least_one / total_questions * 100) if total_questions > 0 else 0
    
    # Save to CSV
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    df = pd.DataFrame(summary_data)
    df.to_csv(csv_path, index=False)
    
    # Log to MLflow if active
    if mlflow.active_run():
        mlflow.log_artifact(csv_path)
    
    # Print summary
    print(f"\nPer-question '{eval_method}' Match count distribution:")
    for item in summary_data:
        print(f"  {item['Match_Count']} matches: {item['Num_Questions']} questions ({item['Percentage']})")
    print(f"\nQuestions with at least one Match: {total_with_at_least_one}/{total_questions} ({coverage_pct:.1f}%)")


def save_all_predictions_json(results: list, json_path: str):
    """
    Save all predictions (valid and invalid) along with selected predictions to a JSON file.
    
    Args:
        results: List of ExperimentResult objects
        json_path: Path to save the JSON file
    """
    all_predictions_data = []
    
    for result in results:
        if result.prediction is None:
            continue
        
        question_id = result.prediction.question.question_id
        question_text = result.prediction.question.text
        db_name = result.prediction.question.db_name
        ground_truth_sql = result.prediction.question.ground_truth
        ground_truth_df = result.prediction.question.ground_truth_df
        
        # Convert ground truth dataframe to records
        ground_truth_result = None
        if ground_truth_df is not None:
            try:
                ground_truth_result = ground_truth_df.to_dict('records')
            except:
                ground_truth_result = str(ground_truth_df)
        
        # Collect valid predictions with match evaluations
        valid_preds = []
        for pred in result.prediction.valid_predictions:
            # Evaluate this prediction against ground truth
            custom_match = compare_df(ground_truth_df, pred.df, None, question_text)
            bird_match = bird_mod_eval(ground_truth_df, pred.df)
            
            # Convert prediction dataframe to records
            pred_result = None
            if pred.df is not None:
                try:
                    pred_result = pred.df.to_dict('records')
                except:
                    pred_result = str(pred.df)
            
            valid_preds.append({
                'model_name': pred.model_name,
                'sql_generated': pred.sql_generated,
                'pydough_generated': pred.pydough_generated,
                'result_df': pred_result,
                'llm_response_time': pred.llm_response_time,
                'db_execution_time': pred.db_execution_time,
                'rollout_id': pred.rollout_id,
                'is_valid': True,
                'exception': None,
                'custom_eval_match': custom_match,
                'bird_eval_match': bird_match
            })
        
        # Collect invalid predictions
        invalid_preds = []
        for pred in result.prediction.invalid_predictions:
            # Try to get result dataframe if it exists
            pred_result = None
            if pred.df is not None:
                try:
                    pred_result = pred.df.to_dict('records')
                except:
                    pred_result = str(pred.df)
            
            invalid_preds.append({
                'model_name': pred.model_name,
                'sql_generated': pred.sql_generated,
                'pydough_generated': pred.pydough_generated,
                'result_df': pred_result,
                'llm_response_time': pred.llm_response_time,
                'db_execution_time': pred.db_execution_time,
                'rollout_id': pred.rollout_id,
                'is_valid': False,
                'exception': str(pred.exception) if pred.exception else None,
                'custom_eval_match': False,
                'bird_eval_match': False
            })
        
        # Get selected prediction info with match evaluations
        selected_pred_info = None
        if result.prediction.selected_prediction:
            selected_custom_match = compare_df(ground_truth_df, result.prediction.selected_prediction.df, None, question_text)
            selected_bird_match = bird_mod_eval(ground_truth_df, result.prediction.selected_prediction.df)
            
            # Convert selected prediction dataframe to records
            selected_result = None
            if result.prediction.selected_prediction.df is not None:
                try:
                    selected_result = result.prediction.selected_prediction.df.to_dict('records')
                except:
                    selected_result = str(result.prediction.selected_prediction.df)
            
            selected_pred_info = {
                'model_name': result.prediction.selected_prediction.model_name,
                'sql_generated': result.prediction.selected_prediction.sql_generated,
                'pydough_generated': result.prediction.selected_prediction.pydough_generated,
                'result_df': selected_result,
                'llm_response_time': result.prediction.selected_prediction.llm_response_time,
                'db_execution_time': result.prediction.selected_prediction.db_execution_time,
                'rollout_id': result.prediction.selected_prediction.rollout_id,
                'custom_eval_match': selected_custom_match,
                'bird_eval_match': selected_bird_match
            }
        
        all_predictions_data.append({
            'question_id': question_id,
            'question': question_text,
            'db_name': db_name,
            'ground_truth_sql': ground_truth_sql,
            'ground_truth_result': ground_truth_result,
            'valid_predictions': valid_preds,
            'invalid_predictions': invalid_preds,
            'selected_prediction': selected_pred_info,
            'total_valid': len(valid_preds),
            'total_invalid': len(invalid_preds),
            'custom_eval_hit': result.compare_hits == 1,
            'bird_eval_hit': result.bird_hits == 1
        })
    
    # Save to JSON
    os.makedirs(os.path.dirname(json_path), exist_ok=True)
    with open(json_path, 'w') as f:
        json.dump(all_predictions_data, f, indent=2)
    
    # Log to MLflow if active
    if mlflow.active_run():
        mlflow.log_artifact(json_path)
    
    print(f"\nAll predictions saved to: {json_path}")


def save_all_predictions_csv(results: list, csv_path: str):
    """
    Save all predictions (valid and invalid) along with selected predictions to a CSV file.
    
    Args:
        results: List of ExperimentResult objects
        csv_path: Path to save the CSV file
    """
    all_rows = []
    
    for result in results:
        if result.prediction is None:
            continue
        
        question_id = result.prediction.question.question_id
        question_text = result.prediction.question.text
        db_name = result.prediction.question.db_name
        ground_truth_sql = result.prediction.question.ground_truth
        
        # Process valid predictions
        for pred in result.prediction.valid_predictions:
            custom_match = compare_df(result.prediction.question.ground_truth_df, pred.df, None, question_text)
            bird_match = bird_mod_eval(result.prediction.question.ground_truth_df, pred.df)
            all_rows.append({
                'question_id': question_id,
                'question': question_text,
                'db_name': db_name,
                'ground_truth_sql': ground_truth_sql,
                'model_name': pred.model_name,
                'sql_generated': pred.sql_generated,
                'pydough_generated': pred.pydough_generated,
                'llm_response_time': pred.llm_response_time,
                'db_execution_time': pred.db_execution_time,
                'rollout_id': pred.rollout_id,
                'is_valid': True,
                'exception': None,
                'custom_eval_match': custom_match,
                'bird_eval_match': bird_match,
                'is_selected': result.prediction.selected_prediction and pred.model_name == result.prediction.selected_prediction.model_name and pred.rollout_id == result.prediction.selected_prediction.rollout_id
            })
        
        # Process invalid predictions
        for pred in result.prediction.invalid_predictions:
            all_rows.append({
                'question_id': question_id,
                'question': question_text,
                'db_name': db_name,
                'ground_truth_sql': ground_truth_sql,
                'model_name': pred.model_name,
                'sql_generated': pred.sql_generated,
                'pydough_generated': pred.pydough_generated,
                'llm_response_time': pred.llm_response_time,
                'db_execution_time': pred.db_execution_time,
                'rollout_id': pred.rollout_id,
                'is_valid': False,
                'exception': str(pred.exception) if pred.exception else None,
                'custom_eval_match': False,
                'bird_eval_match': False,
                'is_selected': False
            })
    
    # Save to CSV
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    df = pd.DataFrame(all_rows)
    df.to_csv(csv_path, index=False)
    
    # Log to MLflow if active
    if mlflow.active_run():
        mlflow.log_artifact(csv_path)
    
    print(f"\nAll predictions saved to CSV: {csv_path}")


def save_selected_predictions_json(results: list, json_path: str):
    """
    Save only the selected predictions to a JSON file.
    
    Args:
        results: List of ExperimentResult objects
        json_path: Path to save the JSON file
    """
    selected_predictions_data = []
    
    for result in results:
        if result.prediction is None or result.prediction.selected_prediction is None:
            continue
        
        selected_pred = result.prediction.selected_prediction
        question = result.prediction.question
        
        # Convert ground truth dataframe to records
        ground_truth_result = None
        if question.ground_truth_df is not None:
            try:
                ground_truth_result = question.ground_truth_df.to_dict('records')
            except:
                ground_truth_result = str(question.ground_truth_df)
        
        # Convert selected prediction dataframe to records
        selected_result = None
        if selected_pred.df is not None:
            try:
                selected_result = selected_pred.df.to_dict('records')
            except:
                selected_result = str(selected_pred.df)
        
        selected_predictions_data.append({
            'question_id': question.question_id,
            'question': question.text,
            'db_name': question.db_name,
            'ground_truth_sql': question.ground_truth,
            'ground_truth_result': ground_truth_result,
            'selected_prediction': {
                'model_name': selected_pred.model_name,
                'sql_generated': selected_pred.sql_generated,
                'pydough_generated': selected_pred.pydough_generated,
                'result_df': selected_result,
                'llm_response_time': selected_pred.llm_response_time,
                'db_execution_time': selected_pred.db_execution_time,
                'rollout_id': selected_pred.rollout_id
            },
            'custom_eval_hit': result.compare_hits == 1,
            'bird_eval_hit': result.bird_hits == 1
        })
    
    # Save to JSON
    os.makedirs(os.path.dirname(json_path), exist_ok=True)
    with open(json_path, 'w') as f:
        json.dump(selected_predictions_data, f, indent=2)
    
    # Log to MLflow if active
    if mlflow.active_run():
        mlflow.log_artifact(json_path)
    
    print(f"\nSelected predictions saved to: {json_path}")


def save_selected_predictions_csv(results: list, csv_path: str):
    """
    Save only the selected predictions to a CSV file.
    
    Args:
        results: List of ExperimentResult objects
        csv_path: Path to save the CSV file
    """
    selected_rows = []
    
    for result in results:
        if result.prediction is None or result.prediction.selected_prediction is None:
            continue
        
        selected_pred = result.prediction.selected_prediction
        question = result.prediction.question
        
        # Evaluate match
        custom_match = compare_df(question.ground_truth_df, selected_pred.df, None, question.text)
        bird_match = bird_mod_eval(question.ground_truth_df, selected_pred.df)
        
        selected_rows.append({
            'question_id': question.question_id,
            'question': question.text,
            'db_name': question.db_name,
            'ground_truth_sql': question.ground_truth,
            'model_name': selected_pred.model_name,
            'sql_generated': selected_pred.sql_generated,
            'pydough_generated': selected_pred.pydough_generated,
            'llm_response_time': selected_pred.llm_response_time,
            'db_execution_time': selected_pred.db_execution_time,
            'rollout_id': selected_pred.rollout_id,
            'custom_eval_match': custom_match,
            'bird_eval_match': bird_match
        })
    
    # Save to CSV
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    df = pd.DataFrame(selected_rows)
    df.to_csv(csv_path, index=False)
    
    # Log to MLflow if active
    if mlflow.active_run():
        mlflow.log_artifact(csv_path)
    
    print(f"\nSelected predictions saved to CSV: {csv_path}")
