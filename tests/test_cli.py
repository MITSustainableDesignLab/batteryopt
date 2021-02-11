import os

import pytest
from click.testing import CliRunner

from batteryopt.cli import batteryopt


class TestCli:
    @pytest.mark.skipif(
        os.environ.get("CI", "False").lower() == "true",
        reason="Skipping this test on CI environment.",
    )
    def test_batteryopt(self):
        runner = CliRunner()
        result = runner.invoke(
            batteryopt,
            [
                "data/demand_aggregated.csv",
                "data/PV_generation_aggregated.csv",
                "output.xlsx",
            ],
        )
        assert result.exit_code == 0
