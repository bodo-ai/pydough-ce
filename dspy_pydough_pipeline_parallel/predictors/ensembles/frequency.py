from predictors.pydough_ensemble import PydoughEnsemble
from predictors.ensembles.heuristics import frequency_based_selection, frequency_based_selection_bird, frequency_based_selection_bird_mod
from predictors.question_prediction import Question

class FrequencyEnsemble(PydoughEnsemble):
    def __init__(self, factories_tries, rng=None, rng_seed=None):
        super().__init__(factories_tries, rng=rng, rng_seed=rng_seed)

    def ensemble_name(self):
        return "FrequencyEnsemble"
    
    def predict(self, question: Question, api_key: str):
        valid_predictions, invalid_predictions = self._create_predictions(question, api_key)
        prediction = frequency_based_selection_bird(valid_predictions, rng=self.rng) if valid_predictions else None 

        return self.build_prediction(question, prediction, valid_predictions, invalid_predictions)
