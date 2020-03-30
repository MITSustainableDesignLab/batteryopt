from click.testing import CliRunner
from batteryopt.cli import batteryopt

class TestCli:
    def test_batteryopt(self):
        runner = CliRunner()
        result = runner.invoke(batteryopt, ["../data/demand_aggregated.csv",
                                            "../data/PV_generation_aggregated.csv",
                                            "output.csv"])
        assert result.exit_code == 0
