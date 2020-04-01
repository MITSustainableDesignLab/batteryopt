from pandas import DataFrame

from batteryopt import create_model, run_model, read_model_results, decision_tree
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


class TestDecisionTree:
    def test_decision_tree(self):
        demand, generation, E_s, P_pv_export, P_discharge, P_charge = decision_tree(
            "../data/demand_aggregated.csv",
            "../data/PV_generation_aggregated.csv",
            E_batt_min=20000,
            E_batt_max=100000,
        )
        df = DataFrame(
            {
                "P_dmd": demand,
                "P_pv": generation,
                "E_s": E_s,
                "P_pv_export": P_pv_export,
                "P_discharge": P_discharge,
                "P_charge": P_charge,
            }
        )
        df.to_excel("tree_results.xlsx")
