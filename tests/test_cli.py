from click.testing import CliRunner
from batteryopt.cli import batteryopt

class TestCli:
    def test_batteryopt(self):
        runner = CliRunner()
        result = runner.invoke(batteryopt, ["output.csv"])
        assert result.exit_code == 0
