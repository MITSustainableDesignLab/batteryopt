import os

import pandas as pd
import pytest

from batteryopt import create_model, read_model_results, run_model


class TestCore:
    @pytest.fixture()
    def model(self):
        """Creates a model from data and yields it to other tests"""
        # First, create the model
        demand = pd.read_csv("data/demand_aggregated.csv").SUM_DEMAND
        pvgen = pd.read_csv("data/PV_generation_aggregated.csv").SUM_GENERATION

        model = create_model(demand, pvgen)
        yield model

    @pytest.mark.skipif(
        os.environ.get("CI", "False").lower() == "true",
        reason="Skipping this test on CI environment.",
    )
    def test_read_model_results(self, model):
        """Tests reading model result as DataFrame"""
        model = run_model(model, solver="gurobi")
        df = read_model_results(model)

        assert ~df.empty
