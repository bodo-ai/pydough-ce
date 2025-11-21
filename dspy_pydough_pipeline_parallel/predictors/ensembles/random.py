from predictors.pydough_ensemble import PydoughEnsemble
import logging
from predictors.question_prediction import Question


class RandomEnsemble(PydoughEnsemble):
    def __init__(self, factories_tries, rng=None, rng_seed=None):
        super().__init__(factories_tries, rng=rng, rng_seed=rng_seed)

    def ensemble_name(self):
        return "RandomEnsemble"
    
    def predict(self, question: Question, api_key: str):
        logger = logging.getLogger(__name__)
        valid_predictions, invalid_predictions = self._create_predictions(question, api_key)
        prediction = self.rng.choice(valid_predictions) if valid_predictions else None   
        logger.debug(f"Valid preds: {len(valid_predictions)}") 
        return self.build_prediction(question, prediction, valid_predictions, invalid_predictions)
    