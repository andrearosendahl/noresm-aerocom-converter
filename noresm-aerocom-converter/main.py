import typer
from typing_extensions import Annotated
from typing import List, Optional
from enum import Enum
from xarray import open_mfdataset, Dataset
import yaml
from pathlib import Path

from conversion_instructions import get_conversion_intstructions

app = typer.Typer()


AVAILABLEMONTHS = [
    "01",
    "02",
    "03",
    "04",
    "05",
    "06",
    "07",
    "08",
    "09",
    "10",
    "11",
    "12",
]

# PERIOD=9999
# PERIOD=1850
LL = 31
FREQUENCY = "monthly"
# converts from sulfuric acid (H2SO4) to SO4 (96/98 MW)
SF1 = "0.9796"
# converts from ammonium sulfate (NH4_2SO4) to SO4 (96/134 MW)
SF2 = "0.7273"
# mass fraction of DST_A3 for d>10 um (from AeroTab, assuming no growth))
F10DSTA3 = "0.23"
# mass fraction of SS_A3 for d>10 um (from AeroTab, assuming no growth))
F10SSA3 = "0.008"
# Rair
RAIR = "287.0"


class Level(str, Enum):
    M = ("ModelLevel",)
    S = ("Surface",)
    C = ("Column",)
    SS = ("SurfaceAtStations",)
    MS = ("ModelLevelAtStations",)
    default = ("INVALIDCOORDINATETYPE",)


def _get_file_list(
    inputdir: str, experiment: str, years: List[str]
) -> dict[str, list[str]]:
    files = {}
    for year in years:
        file_year = []
        for month in range(1, 13):
            file_year.append(
                f"{inputdir}/atm/hist/{experiment}.cam.h0.{year}-{month:02}.nc"
            )
        files[year] = file_year

    return files


def _open_year_dataset(files: list[str]) -> Dataset:
    data = open_mfdataset(paths=files, decode_times=False)
    return data


def _make_aerocom_dataset(
    data: Dataset,
    variable: str,
    instruction: dict[str, str],
    year: str,
) -> Dataset:
    command = f"data.assign({variable} = lambda x: {instruction['command']})"
    new_data = eval(command)
    new_data = new_data[[variable, "time", "time_bnds", "lat", "lon"]]
    new_data.time.attrs["units"] = f"days since {year}-01-01 00:00:00"
    return new_data


def save_aerocom_data(
    data: Dataset, outdir: str, fullname: str, aerocomname: str, level: str, year: str
):
    out_file = (
        f"{outdir}/aerocom3_{fullname}_{aerocomname}_{level}_{year}_{FREQUENCY}.nc"
    )
    typer.echo(f"Saving file to {out_file}")
    data.to_netcdf(out_file)


def _convert(
    inputdir: str,
    outputdir: str,
    experiment: str,
    fullname: str,
    baseyear: int,
    years: List[str],
    variables: Optional[List[str]] = None,
) -> None:
    for i, year in enumerate(years):

        years[i] = f"{int(year):04}"

    instructions = get_conversion_intstructions(LL)
    if variables is None:
        variables = list(instructions.keys())
    files = _get_file_list(inputdir, experiment, years)
    for year in files:
        typer.echo(f"Converting for year {year}")
        data = _open_year_dataset(files[year])
        for var in instructions:
            if var in variables:
                new_data = _make_aerocom_dataset(
                    data, var, instructions[var], f"{baseyear:04}"
                )
                save_aerocom_data(
                    new_data,
                    outputdir,
                    fullname,
                    var,
                    instructions[var]["coordinates"],
                    f"{baseyear + int(year):04}",
                )


@app.command()
def from_file(path: Annotated[str, typer.Argument(rich_help_panel="Path to ")]):
    if Path(path).exists():
        with open(path, "r") as f:
            arguments = yaml.safe_load(f)

        _convert(**arguments)


@app.command()
def convert(
    inputdir: Annotated[str, typer.Argument(rich_help_panel="Input Directory")],
    outputdir: Annotated[str, typer.Argument(rich_help_panel="Output directory")],
    experiment: Annotated[str, typer.Argument(rich_help_panel="Experiment Name")],
    fullname: Annotated[str, typer.Argument(rich_help_panel="")],
    baseyear: Annotated[int, typer.Argument(rich_help_panel="Reference Year")],
    years: Annotated[List[str], typer.Argument(rich_help_panel="Years")],
    variables: Annotated[
        Optional[List[str]],
        typer.Option(
            rich_help_panel="Which variables to convert. If non is given, then everything is converted"
        ),
    ],
) -> None:
    _convert(inputdir, outputdir, experiment, fullname, baseyear, years, variables)


if __name__ == "__main__":
    app()
