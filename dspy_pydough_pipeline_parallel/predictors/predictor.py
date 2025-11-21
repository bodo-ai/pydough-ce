import dspy
import time
import logging
from utils.caching.sqlite_cache import SqliteCache
from utils.utils import extract_python_code, create_error_prediction
from utils.helpers.pydough_helper import Pydough_helper
from predictors.question_prediction import Question, Prediction
from abc import ABC, abstractmethod
from dataclasses import dataclass


class Text2Pydough(dspy.Signature):
    """Based on database query described in English, use the context and schema to generate pydough code."""
    query: str = dspy.InputField(desc="Contains the english query")
    context: str = dspy.InputField(desc="Contains a reference description of the pydough language")
    db_schema: str = dspy.InputField(desc="Contains the schema of the database")
    feedback: str = dspy.InputField(desc="Contains feedback on previous attempts, if any", default="No previous feedback")
    pydough_failed: str = dspy.InputField(desc="pydough preveiusly generated that failed on execution", default="No previous failures")
    answer: str = dspy.OutputField(desc="Contains the pydough code that will execute the query, taking into account the context, schema and if exists, the feedback and previous failures.")
    


logger = logging.getLogger(__name__)        

class AbstractPredictor(ABC):   
    @abstractmethod
    def predict(self, question: Question, rollout_id: int = None) -> Prediction:
        pass


@dataclass
class Rollout_config:
    rollout_id: int
    experiment_name: str


class PydoughPredictor(AbstractPredictor):

    def __init__(self, model, cache_path, temperature, context, db_base_path, dspy_cache,experiment_name, retries=3):
        self.model = model
        self.temperature = temperature
        self.context = context
        self.cache = SqliteCache(cache_path)
        self.db_base_path = db_base_path
        self.dspy_cache = dspy_cache
        self.experiment_name = experiment_name
        self.retries = retries 


    def generate_prediction_with_retries(self, question: Question, rollout_id: int, api_key: str) -> Prediction:

        rollout_config = Rollout_config(rollout_id=rollout_id, experiment_name=self.experiment_name)
        lm = dspy.LM(cache=self.dspy_cache, model=self.model, api_key=api_key, temperature=self.temperature, max_tokens=None)
        dspy.settings.configure(lm=lm)
        llm_start_time = time.time()


        with dspy.settings.context(lm=lm):  
            feedback_history = []   
            gen_pydough_code = "no previous pydough code"
            full_feedback = "no feedback yet"
            
            for i in range(self.retries):
                if i > 0:
                    current_feedback = f"""Iteration #{i + 1}: Previous attempt resulted in invalid SQL: {gen_sql.exception}. 
                    Previous pydough code that failed: {gen_pydough_code}"""
                    feedback_history.append(current_feedback)               
                    full_feedback = "\n\n".join(feedback_history) 

                qa = dspy.ChainOfThought(Text2Pydough)
                response = qa(
                    query=question.text,
                    context=self.context,
                    db_schema=question.db_schema, 
                    feedback=full_feedback, 
                    pydough_failed=gen_pydough_code,
                    config=rollout_config.__dict__
                )
                
                gen_pydough_code = extract_python_code(response.answer)
                pydough_helper = Pydough_helper(question.metadata_path, question.db_name)
                gen_sql = pydough_helper.generate_sql(gen_pydough_code)
                
                if gen_sql.is_valid:
                    llm_response_time = time.time() - llm_start_time
                    gen_sql = gen_sql.sql                 
                    db_execution_start_time = time.time()
                    df = self.cache.execute(question.db_path, gen_sql)
                    db_execution_time = time.time() - db_execution_start_time
                    
                    return Prediction(
                        question=question,
                        sql_generated=gen_sql,
                        pydough_generated=gen_pydough_code,
                        df=df,
                        llm_response_time=llm_response_time,
                        model_name=self.model,
                        db_execution_time=db_execution_time,
                        rollout_id=rollout_id
                    )
            
            llm_response_time = time.time() - llm_start_time
            return create_error_prediction(
                question=question, 
                pydough_generated=gen_pydough_code,
                exception=gen_sql.exception,
                llm_response_time=llm_response_time,
                model_name=self.model,
                rollout_id=rollout_id
            )


    def predict(self, question: Question, rollout_id: int, api_key: str) -> Prediction:

        try:
            return self.generate_prediction_with_retries(question, rollout_id, api_key)
        except Exception as e:
            return create_error_prediction(
                question=question,
                model_name=self.model,
                rollout_id=rollout_id,
                exception=str(e)
            )
        

class PydoughPredictionFactory:
    def __init__(self, model: str ,cache_path: str, temperature: float, 
                 context: str, db_base_path: str, dspy_cache: bool, experiment_name: str, retries: int):
        self.model = model
        self.cache_path = cache_path
        self.temperature = temperature
        self.context = context
        self.db_base_path = db_base_path
        self.dspy_cache = dspy_cache
        self.experiment_name = experiment_name
        self.retries = retries

    
    def create(self):
        return PydoughPredictor(
            model=self.model,
            cache_path=self.cache_path,
            temperature=self.temperature,
            context=self.context,
            db_base_path=self.db_base_path,
            dspy_cache=self.dspy_cache,
            experiment_name=self.experiment_name,
            retries=self.retries
        )
    
