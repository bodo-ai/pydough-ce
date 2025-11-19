from predictors.predictor import AbstractPredictor
from predictors.gradio_predictor import GradioPredictor
from predictors.question_prediction import PredictionEnsemble, Prediction, Question
from evaluation.eval import df_bird_eval
from utils.utils import create_error_prediction 
from collections import defaultdict
from typing import Optional
import random

class PydoughEnsemble(AbstractPredictor):
    def __init__(self, factories_tries, rng: Optional[random.Random] = None, rng_seed: Optional[int] = None):
        self.factories_tries = factories_tries
        self.predictors = []
        # Initialize a per-ensemble RNG
        if rng is not None:
            self.rng = rng
        elif rng_seed is not None:
            self.rng = random.Random(rng_seed)
        else:
            self.rng = random.Random(12345)

        for factory, count in self.factories_tries:
            for _ in range(count):
                predictor = factory.create()
                self.predictors.append(predictor)



    def _create_predictions(self, question: Question, api_key: str):
            valid_predictions = []
            invalid_predictions = []
            rollout_counters = defaultdict(int)  # per-model rollout counter
            for predictor in self.predictors:
                # use predictor.model as the key so each predictor type has its own counter

                model = str(getattr(predictor, "model", id(predictor)))
                architecture = ("basic")

                if isinstance(predictor, GradioPredictor):
                    architecture = str(getattr(predictor, "architecture", id(predictor)))
                    
                key = model + architecture
                rollout_id = rollout_counters[key]
                rollout_counters[key] += 1

                try:
                    prediction = predictor.predict(question, rollout_id=rollout_id, api_key=api_key)
                    if prediction.is_valid():
                        valid_predictions.append(prediction)  
                    else:
                        invalid_predictions.append(prediction)
                except Exception as e:
                    error = "this shouldn't happen: "+str(e)
                    prediction = create_error_prediction(question=question, model_name=predictor.model, exception=error, rollout_id=rollout_id)
                    invalid_predictions.append(prediction)
            return valid_predictions, invalid_predictions
    


    def ensemble_name(self):
        return "AbstractEnsemble :*(, you should not see this. " 
    

    def build_prediction(self, question: Question, prediction: Prediction, valid_predictions: list, invalid_predictions: list):
        response_time = 0.0
        for p in valid_predictions + invalid_predictions:
            response_time += p.llm_response_time

        if prediction is not None:
            result = PredictionEnsemble(
                question=question,
                sql_generated=prediction.sql_generated,
                pydough_generated=prediction.pydough_generated,
                df=prediction.df,
                llm_response_time=response_time,
                model_name=f"{self.ensemble_name()}/{prediction.model_name}"
            )
            result.valid_predictions = valid_predictions
            result.invalid_predictions = invalid_predictions
            result.selected_prediction = prediction
            return result

        else:
            result = PredictionEnsemble(
                question=question,
                sql_generated=None,
                pydough_generated="",
                df=None,
                llm_response_time=response_time,
                model_name=self.ensemble_name()
            )

            result.valid_predictions = valid_predictions
            result.invalid_predictions = invalid_predictions
            return result

    def same_prediction_check(self, valid_predictions: list):
        all_same_df = True
        if len(valid_predictions) > 1:
            first_df = valid_predictions[0].df
            for pred in valid_predictions[1:]:
                if not df_bird_eval(pred.df, first_df):
                    all_same_df = False
                    break
        return all_same_df