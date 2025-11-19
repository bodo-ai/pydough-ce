import pandas as pd
import os
import multiprocessing as mp
from predictors.predictor import AbstractPredictor
from predictors.question_prediction import Question, Prediction
from utils.utils import write_results, Exception_info,save_exceptions_report
from evaluation.eval import compare_df, bird_mod_eval, df_bird_eval, bird_upper_bound, custom_upper_bound, mod_bird_upper_bound
import logging
from dataclasses import dataclass
import json
import mlflow
import traceback
from utils.helpers.mlflow_tracking import process_individuals_results, process_per_question_match_distribution, save_all_predictions_json, save_all_predictions_csv, save_selected_predictions_json, save_selected_predictions_csv


@dataclass
class ExperimentResult: 
    compare_hits: int = 0
    bird_hits: int = 0
    custom_bird_hits: int = 0  
    upper_bound_custom_bird: int = 0
    upper_bound_compare_df: int = 0
    upper_bound_bird_hits: int = 0 
    timeouts: int = 0
    query_error: int = 0
    prediction: Prediction = None


log_level = logging.INFO #Change level on your needs

logging.basicConfig(
    level=log_level,
    format='%(message)s',
    filename='debug.log',
    filemode='w'  
)

def run_single_question(question: Question, p: AbstractPredictor, api_key: str, csv_path: str) -> dict:
    
    pred = p.predict(question, api_key=api_key)
    result = ExperimentResult()
    result.prediction = pred
    if pred.selected_prediction is None:
        write_results(pred.invalid_predictions[0], "Query error", "Query error", csv_path)
        result.query_error +=1
        return result
    
    custom_cmp = compare_df(question.ground_truth_df, pred.selected_prediction.df, None, question.text)
    bird_cmp = df_bird_eval(question.ground_truth_df, pred.selected_prediction.df)
    mod_bird_cmp = bird_mod_eval(pred.selected_prediction.df, question.ground_truth_df)

    write_results(pred.selected_prediction, str(custom_cmp), str(bird_cmp), csv_path)
    
    bird_upper = bird_upper_bound(question, pred.valid_predictions)
    custom_upper = custom_upper_bound(question, pred.valid_predictions)
    
    if bird_upper: result.upper_bound_bird_hits = 1
    if custom_upper: result.upper_bound_compare_df = 1


    if custom_cmp: result.compare_hits= 1
    if bird_cmp: result.bird_hits = 1
    if mod_bird_cmp: result.custom_bird_hits = 1 
    
    if "Exec_error" in pred.df.columns and "timed out" in pred.df.iloc[0, 0]: 
        result.timeouts = 1   
    return result

def worker(question: Question, ensemble: AbstractPredictor, api_key: str, csv_path: str):
    try:
        result = run_single_question(question, ensemble, api_key, csv_path)
        return result
    except Exception as e:
        exception_info = Exception_info(
            question=question,
            exception=str(e),
            traceback=traceback.format_exc()
        )
        return exception_info


def parallel_process_questions(ensemble: AbstractPredictor, questions: list[Question], api_keys: list, 
                               experiment_dataset: str, processes_per_key: int, results_path: str):
    
    num_processes = len(api_keys) * processes_per_key  
    os.makedirs(results_path, exist_ok=True)
    
    api_keys = [key for key in api_keys for _ in range(processes_per_key)]

    args_list = [
        (question, ensemble, api_keys[i % num_processes], f"{results_path}/results_process_{i % num_processes}.csv")
        for i, question in enumerate(questions)
    ]
    
    with mp.Pool(processes=num_processes) as pool:
        results = pool.starmap(worker, args_list, chunksize=1)
    
    experiment_results = []
    exception_list = []
    
    for result in results:
        if isinstance(result, Exception_info):
            exception_list.append(result)
        else:
            experiment_results.append(result)
    
    total_questions = len(questions)
    process_results(experiment_results, experiment_dataset, total_questions, f"{results_path}/summary.json")
    merge_csv_results(results_path)    
    process_individuals_results(experiment_results, experiment_dataset, total_questions, f"{results_path}/model_statistics.csv")
    process_per_question_match_distribution(experiment_results, experiment_dataset, total_questions, f"{results_path}/match_distribution_custom.csv", eval_method="eval_custom")
    process_per_question_match_distribution(experiment_results, experiment_dataset, total_questions, f"{results_path}/match_distribution_bird.csv", eval_method="eval_bird")
    save_all_predictions_json(experiment_results, f"{results_path}/all_predictions.json")
    save_all_predictions_csv(experiment_results, f"{results_path}/all_predictions.csv")
    save_selected_predictions_json(experiment_results, f"{results_path}/selected_predictions.json")
    save_selected_predictions_csv(experiment_results, f"{results_path}/selected_predictions.csv")
    save_exceptions_report(exception_list, f"{results_path}/exceptions_report.csv")



def process_results(results: list[ExperimentResult], experiment_dataset: str, total_questions: int, csv_path: str):
    
    total_compare_hits = sum(r.compare_hits for r in results)
    total_bird_hits = sum(r.bird_hits for r in results)
    total_mod_bird_hits = sum(r.custom_bird_hits for r in results)

    upper_bound_compare_df = sum(r.upper_bound_compare_df for r in results)
    upper_bound_bird = sum(r.upper_bound_bird_hits for r in results)
    upper_bound_mod_bird = sum(r.upper_bound_bird_hits for r in results)

    total_timeouts = sum(r.timeouts for r in results)
    total_query_error = sum(r.query_error for r in results)

    data_to_write = {
        "Experiment dataset": experiment_dataset,

        "Total questions": total_questions,
        "Total custom hits" : total_compare_hits,
        "Total bird hits": total_bird_hits,

        "Upper_bound_compare_df %": upper_bound_compare_df / total_questions * 100,
        "Upper_bound_bird_hits %" : upper_bound_bird / total_questions * 100,
        "Upper_bound_sutom_bird_hits %" : upper_bound_mod_bird / total_questions * 100,

        "Acuraccy custom %": total_compare_hits / total_questions * 100,
        "Acuraccy bird %": total_bird_hits / total_questions * 100,
        "Acuraccy mod bird %": total_mod_bird_hits / total_questions * 100,


        "Total timeouts question": total_timeouts,
        "Total Query error": total_query_error,
    }
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)

    with open(csv_path, "w") as json_file:
        json.dump(data_to_write, json_file, indent=4)
    
    # Log to MLflow if there's an active run


    if mlflow.active_run():
        # Log aggregate metrics
        mlflow_metrics = {
            "total_questions": total_questions,

            "custom_eval_hits": total_compare_hits,
            "bird_eval_hits": total_bird_hits,
            "mod_bird_eval_hits" : total_mod_bird_hits,

            "custom_accuracy": total_compare_hits / total_questions if total_questions > 0 else 0.0,
            "bird_accuracy": total_bird_hits / total_questions if total_questions > 0 else 0.0,
            "mod_bird_accuracy": total_mod_bird_hits / total_questions if total_questions > 0 else 0.0,

            "upper_bound_custom": upper_bound_compare_df / total_questions if total_questions > 0 else 0.0,
            "upper_bound_bird": upper_bound_bird / total_questions if total_questions > 0 else 0.0,
            "upper_bound_mod_bird": upper_bound_mod_bird / total_questions if total_questions > 0 else 0.0,

            "upper_bound_custom_count": upper_bound_compare_df,
            "upper_bound_bird_count": upper_bound_bird,
            "upper_bound_mod_bird_count": upper_bound_mod_bird,


            "timeout_count": total_timeouts,
            "query_error_count": total_query_error,
            "timeout_rate": total_timeouts / total_questions if total_questions > 0 else 0.0,
            "query_error_rate": total_query_error / total_questions if total_questions > 0 else 0.0,
        }
        mlflow.log_metrics(mlflow_metrics)
            
        # Log summary as artifact
        mlflow.log_artifact(csv_path)


def merge_csv_results(results_path: str, merged_filename: str = "results_merged.csv"):
    partial_csvs = [
        os.path.join(results_path, f)
        for f in os.listdir(results_path)
        if f.startswith("results_process_") and f.endswith(".csv")
    ]

    df_list = [
        pd.read_csv(csv, dtype=str, keep_default_na=False, na_filter=False)
        for csv in partial_csvs
        if os.path.getsize(csv) > 0
    ]
    merged_df = pd.concat(df_list, ignore_index=True)

    merged_path = os.path.join(results_path, merged_filename)
    merged_df.to_csv(merged_path, index=False)

    for csv in partial_csvs:
        os.remove(csv)

    return merged_path

