from dataclasses import dataclass
import os
from typing import Optional
import pandas as pd
from utils.caching.sqlite_cache import SqliteCache
from pydough import parse_json_metadata_from_file
from utils.generate_markdown import generate_markdown_from_metadata


@dataclass
class Question:
    question_id: int = 0
    text: str = ""
    ground_truth: str = ""
    db_name: str = ""
    db_path: str = ""
    metadata_name: str = ""
    metadata_path: str = ""
    dataset_name: str = ""
    ground_truth_df: pd.DataFrame = None
    db_schema: str = ""
    md_map = None  

    def set_properties(self, row: pd.Series, db_base_path: str, metadata_base_path: str) -> None:
        self.question_id = row["question_index"]
        self.text = row["question"]
        self.ground_truth = row["sql"]

        self.db_name = row["db_name"]
        self.dataset_name = row["dataset_name"]

        self.db_path = os.path.join(db_base_path, self.dataset_name, 'databases', self.db_name, f"{self.db_name}.sqlite")
        self.metadata_path = os.path.join(metadata_base_path, self.dataset_name, "metadata", f"{self.db_name}_graph_enriched.json")  

        graph = parse_json_metadata_from_file(self.metadata_path, self.db_name)

        self.db_schema = generate_markdown_from_metadata(graph)

@dataclass
class Prediction:
    """Single prediction result with all necessary context"""
    question: Question
    sql_generated: Optional[str]
    pydough_generated: str 
    df: pd.DataFrame
    llm_response_time: float = 0.0
    model_name: str = ""
    exception: Exception = None
    db_execution_time: float = 0.0
    rollout_id: int = 0
    

    def is_valid(self) -> bool:
        return self.df is not None and self.sql_generated is not None
    
    def get_question(self):
        return self.question.text
    
    
class PredictionEnsemble(Prediction):
    def __init__(self, question: Question, sql_generated: Optional[str], pydough_generated: str,
                 df: Optional[pd.DataFrame], llm_response_time: float, model_name: str,
                 exception: Exception = None, db_execution_time: float = 0.0, rollout_id: int = 0):
        super().__init__(question, sql_generated, pydough_generated, df, llm_response_time, 
                        model_name, exception, db_execution_time, rollout_id)
        
        
        self.valid_predictions: list[Prediction] = []
        self.invalid_predictions: list[Prediction] = []
        self.selected_prediction: Optional[Prediction] = None

    def is_valid(self) -> bool:
        return len(self.valid_predictions) > 0



def prepare_questions(db_base_path: str, metadata_base_pat: str, df: pd.Series, cache_path: str) -> list[Question]:
    cache = SqliteCache(cache_path)
    questions = []
    for _, row in df.iterrows():
        question = Question()
        question.set_properties(row, db_base_path, metadata_base_pat)
        question.ground_truth_df = cache.execute(question.db_path, question.ground_truth)
        questions.append(question)
    return questions