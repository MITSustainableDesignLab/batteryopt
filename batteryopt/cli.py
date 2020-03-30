import click

from batteryopt import run_model, read_model_results


@click.command()
@click.argument("demand", type=click.File("r"))
@click.argument("pvgen", type=click.File("r"))
@click.option(
    "--p", default=0.0002624, type=click.FLOAT, help="Price of electricity $/Wh"
)
@click.option("--f", default=0.0000791, type=click.FLOAT, help="Feed in tariff $/Wh")
@click.option(
    "--cmin", default=100, type=click.FLOAT, help="minimum battery charging power (W)"
)
@click.option(
    "--cmax", default=32000, type=click.FLOAT, help="maximum battery charging power (W)"
)
@click.option(
    "--dmin",
    default=100,
    type=click.FLOAT,
    help="minimum battery discharging power (W)",
)
@click.option(
    "--dmax",
    default=32000,
    type=click.FLOAT,
    help="maximum battery discharging power (W)",
)
@click.option("--ceff", default=1, type=click.FLOAT, help="charging efficiency")
@click.option("--deff", default=1, type=click.FLOAT, help="discharging efficiency")
@click.option(
    "--smin",
    default=20000,
    type=click.FLOAT,
    help="battery minimum energy state of charge (Wh)",
)
@click.option(
    "--smax",
    default=100000,
    type=click.FLOAT,
    help="battery maximum energy state of charge (Wh)",
)
@click.argument("out", type=click.Path(file_okay=True), default="Pbought_aggregated")
def batteryopt(
    demand, pvgen, p, f, cmin, cmax, dmin, dmax, ceff, deff, smin, smax, out
):
    """Runs battery opt"""
    from batteryopt import create_model

    model = create_model(
        demand, pvgen, p, f, cmin, cmax, dmin, dmax, ceff, deff, smin, smax
    )
    model = run_model(model)
    # saving results to file
    df = read_model_results(model)
    df.to_excel(out, index_label="Time Step")
