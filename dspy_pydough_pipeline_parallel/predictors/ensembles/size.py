from predictors.pydough_ensemble import PydoughEnsemble
from predictors.ensembles.heuristics import size_based_selection
from predictors.question_prediction import Question

class SizeEnsemble(PydoughEnsemble):
    def __init__(self, factories_tries, rng=None, rng_seed=None):
        super().__init__(factories_tries, rng=rng, rng_seed=rng_seed)

    def ensemble_name(self):
        return "SizeEnsemble"
    
    def predict(self, question: Question, api_key: str):
        valid_predictions, invalid_predictions = self._create_predictions(question, api_key)
        prediction = size_based_selection(valid_predictions, tb=True, rng=self.rng) if valid_predictions else None 

        return self.build_prediction(question, prediction, valid_predictions, invalid_predictions)
    