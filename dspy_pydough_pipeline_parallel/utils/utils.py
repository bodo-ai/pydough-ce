import os
import re
import textwrap
import json
import pandas as pd
import dspy
from dataclasses import dataclass
from predictors.question_prediction import Prediction, PredictionEnsemble, Question


@dataclass
class Predictions:
    predictions_list :list[Prediction]


@dataclass
class Exception_info:
    question: Question
    exception : str = ""
    traceback : str = ""

def save_exceptions_report(exception_list: list[Exception_info], csv_path: str = "exceptions_report.csv"):
    if not exception_list:
        print("No exceptions were generated during execution.")
        return
       
    exception_data_list = []
    for exc_info in exception_list:
        exception_data = {
            'question_id': exc_info.question.question_id if hasattr(exc_info.question, 'question_id') else 'N/A',
            'question_text': exc_info.question.text if hasattr(exc_info.question, 'text') else str(exc_info.question),
            'db_name': exc_info.question.db_name if hasattr(exc_info.question, 'db_name') else 'N/A',
            'dataset_name': exc_info.question.dataset_name if hasattr(exc_info.question, 'dataset_name') else 'N/A',
            'exception': exc_info.exception,
            'traceback': exc_info.traceback
        }
        exception_data_list.append(exception_data)
    exceptions_df = pd.DataFrame(exception_data_list)
    if os.path.exists(csv_path):
        existing_df = pd.read_csv(csv_path)
        combined_df = pd.concat([existing_df, exceptions_df], ignore_index=True)
    else:
        combined_df = exceptions_df
    combined_df.to_csv(csv_path, index=False)
    print(f"Total exceptions generated: {len(exception_list)}")


def extract_python_code(text):
    if not isinstance(text, str):
        return ""    
    matches = re.findall(r"```(?:\w+)?\s*\n(.*?)\s*```", text, re.DOTALL)
    if matches:
        return textwrap.dedent(matches[-1]).strip()
    answer_match = re.search(r"Answer:\s*(.*)", text, flags=re.IGNORECASE | re.DOTALL)
    if answer_match:
        answer_text = answer_match.group(1).strip()
        return answer_text 
    return text



def write_results(prediction: Prediction, compare_df_evaluation: str, bird_evaluation: str, csv_path="results.csv"):
    result_data = {
        'question_id': prediction.question.question_id,
        'question': prediction.question.text,
        'db_name': prediction.question.db_name,
        'dataset_name': prediction.question.dataset_name,
        'model': prediction.model_name,
        'rollout_id': prediction.rollout_id,
        'pydough_code': prediction.pydough_generated,
        'sql_generated': prediction.sql_generated,
        'ground_truth': prediction.question.ground_truth, 
        'gen_df': prediction.df,
        'gold_df' : prediction.question.ground_truth_df,
        'llm_response_time': prediction.llm_response_time,
        'db_execution_time': prediction.db_execution_time,
        'evaluation': compare_df_evaluation,
        'bird_evaluation' : bird_evaluation,
        'exception': prediction.exception
    } 
    
    result_df = pd.DataFrame([result_data])
    
    if os.path.exists(csv_path):
        existing_df = pd.read_csv(csv_path)
        combined_df = pd.concat([existing_df, result_df], ignore_index=True)
    else:
        combined_df = result_df
    
    combined_df.to_csv(csv_path, index=False)


def write_ensemble_results(prediction_ensemble: PredictionEnsemble, csv_path="all_runs.csv"):
    all_predictions = []
    
    predictions_to_write = []
    if prediction_ensemble.valid_predictions:
        predictions_to_write.extend(prediction_ensemble.valid_predictions)
    if prediction_ensemble.invalid_predictions:
        predictions_to_write.extend(prediction_ensemble.invalid_predictions)
    
    if not predictions_to_write:
        predictions_to_write = [prediction_ensemble]
    
    for pred in predictions_to_write:
        result_data = {
            'question_id': pred.question.question_id,
            'question': pred.question.text,
            'db_name': pred.question.db_name,
            'dataset_name': pred.question.dataset_name,
            'rollout_id': pred.rollout_id,           
            'model': pred.model_name,
            'pydough_code': pred.pydough_generated,
            'sql_generated': pred.sql_generated,
            'ground_truth': pred.question.ground_truth,
            'gen_df': pred.df if pred.df is not None else None,
            'gold_df': pred.question.ground_truth_df if pred.question.ground_truth_df is not None else None,
            'llm_response_time': pred.llm_response_time,
            'db_execution_time': pred.db_execution_time,
            'is_valid': pred.is_valid(),
            'exception': pred.exception
        }
        all_predictions.append(result_data)
    
    result_df = pd.DataFrame(all_predictions)

    if os.path.exists(csv_path):
        existing_df = pd.read_csv(csv_path)
        combined_df = pd.concat([existing_df, result_df], ignore_index=True)
    else:
        combined_df = result_df

    combined_df.to_csv(csv_path, index=False)


def create_error_prediction(
    question=None,
    model_name="",
    rollout_id=-1,
    pydough_generated=None,
    sql_generated=None,
    df=None,
    llm_response_time=0.0,
    db_execution_time=0.0,
    exception="",
):
    return Prediction(
        question=question,
        model_name=model_name,
        rollout_id=rollout_id,
        pydough_generated=pydough_generated,
        sql_generated=sql_generated,
        df=df,
        llm_response_time=llm_response_time,
        db_execution_time=db_execution_time,
        exception= exception
    )


def create_valid_prediction( question, model_name, rollout_id, pydough_generated,
                            sql_generated,df,llm_response_time,db_execution_time):
    return Prediction(
        question=question,
        model_name=model_name,
        rollout_id=rollout_id,
        pydough_generated=pydough_generated,
        sql_generated=sql_generated,
        df=df,
        llm_response_time=llm_response_time,
        db_execution_time=db_execution_time,
        exception=None
    )



