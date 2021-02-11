import click
from path import Path

from batteryopt import run_model, read_model_results


@click.command()
@click.argument("demand", type=click.File("r"))
@click.argument("pvgen", type=click.File("r"))
@click.option(
    "--p",
    default=0.0002624,
    type=click.FLOAT,
    help="Price of electricity $/Wh",
    show_default=True,
)
@click.option(
    "--f",
    default=0.0000791,
    type=click.FLOAT,
    help="Feed in tariff $/Wh",
    show_default=True,
)
@click.option(
    "--cmin",
    default=100,
    type=click.FLOAT,
    help="minimum battery charging power (W)",
    show_default=True,
)
@click.option(
    "--cmax",
    default=32000,
    type=click.FLOAT,
    help="maximum battery charging power (W)",
    show_default=True,
)
@click.option(
    "--dmin",
    default=100,
    type=click.FLOAT,
    help="minimum battery discharging power (W)",
    show_default=True,
)
@click.option(
    "--dmax",
    default=32000,
    type=click.FLOAT,
    help="maximum battery discharging power (W)",
    show_default=True,
)
@click.option(
    "--ceff", default=1, type=click.FLOAT, help="charging efficiency", show_default=True
)
@click.option(
    "--deff",
    default=1,
    type=click.FLOAT,
    help="discharging efficiency",
    show_default=True,
)
@click.option(
    "--smin",
    default=20000,
    type=click.FLOAT,
    help="battery minimum energy state of charge (Wh)",
    show_default=True,
)
@click.option(
    "--smax",
    default=100000,
    type=click.FLOAT,
    help="battery maximum energy state of charge (Wh)",
    show_default=True,
)
@click.argument("out", type=click.Path(file_okay=True), default="optim_results.xlsx")
def batteryopt(
    demand, pvgen, p, f, cmin, cmax, dmin, dmax, ceff, deff, smin, smax, out
):
    """DEMAND and PVGEN are both csv files with a single column. Headers must be
    named SUM_DEMAND and SUM_GENERATION respectively. OUT is the name of the
    generated results excel file (default="optim_results.xlsx").

    Example:
    batteryopt data/demand_aggregated.csv data/PV_generation_aggregated.csv --p 0.00085
    """
    from batteryopt import create_model
    import pandas as pd

    demand = pd.read_csv(demand).SUM_DEMAND
    pvgen = pd.read_csv(pvgen).SUM_GENERATION

    model = create_model(
        demand, pvgen, p, f, cmin, cmax, dmin, dmax, ceff, deff, smin, smax
    )
    model = run_model(model, solver="gurobi")
    # saving results to file
    df = read_model_results(model)
    df.to_excel(out, index_label="Time Step")
    print(f"solver logs available at {Path(model.optim.options['logfile']).abspath()}")
    print(f"results file generated at {Path(out).abspath()}")
