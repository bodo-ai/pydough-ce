from evaluation.prompt_evaluation import parallel_process_questions
from pathlib import Path
from dotenv import load_dotenv
import pandas as pd
import os
from predictors.predictor import PydoughPredictionFactory
from predictors.question_prediction import prepare_questions
from predictors.ensembles.frequency import FrequencyEnsemble
from predictors.ensembles.density import DensityEnsemble
from predictors.ensembles.random import RandomEnsemble

import time


if __name__ == "__main__":

    processes_per_key = 3
    experiment_name = "Bird_COT"
    results_path = "results"
    
    env = load_dotenv()
    
    api_keys = [
        os.getenv("GOOGLE_API_KEY_1"),
        os.getenv("GOOGLE_API_KEY_2"),
        os.getenv("GOOGLE_API_KEY_3"),
        os.getenv("GOOGLE_API_KEY_4"),
        os.getenv("GOOGLE_API_KEY_5"),
        os.getenv("GOOGLE_API_KEY_6")
    ] 

    db_base_path = "data/datasets/"  
    metadata_base_path = "data/datasets/"

    
    cache_path = f"cache/{experiment_name}"  
    questions_df = pd.read_csv("data/questions/bird_30.csv")
    context = Path("data/prompts/cheatsheet_8_1.md").read_text() 


    factory1 = PydoughPredictionFactory(
        model='gemini/gemini-2.5-pro',
        temperature=0.2,
        context=context,
        cache_path=cache_path,
        db_base_path=db_base_path,
        dspy_cache = True,
        experiment_name=experiment_name,
        retries=3
    )

    questions = prepare_questions(db_base_path, metadata_base_path, questions_df, cache_path)
    ensemble = FrequencyEnsemble([(factory1, 3)])  

    start_time = time.perf_counter()
    parallel_process_questions(ensemble, questions, api_keys, experiment_name,processes_per_key, results_path)
    end_time = time.perf_counter()
    elapsed = end_time - start_time
        
    print(f"Test duration: {elapsed:.2f} s")