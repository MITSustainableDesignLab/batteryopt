from batteryopt import create_model, run_model, read_model_results
import pytest


class TestCore:
    @pytest.fixture()
    def model(self):
        """Creates a model from data and yields it to other tests"""
        # First, create the model
        model = create_model(
            "../data/demand_aggregated.csv", "../data/PV_generation_aggregated.csv"
        )
        yield model

    def test_read_model_results(self, model):
        """Tests reading model result as DataFrame"""
        model = run_model(model)
        df = read_model_results(model)

        assert ~df.empty
