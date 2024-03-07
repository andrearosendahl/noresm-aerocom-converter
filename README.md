# noresm-aerocom-converter (NAC)
Small tool for converting [NorESM](https://www.noresm.org/) output for the use in [AeroTools and PyAerocom](https://github.com/metno/pyaerocom).

AeroTools is a model evaluation toolkit made by the Norwegian Meteorological Institute, and is primarily used to evaluate airpollution models, like [EMEP](https://www.emep.int/). While supporting a handfull of modeldata formats, the main format is *Aerocom3* format.

NAC is a small tool -- part of AeroTools -- meant to make it easier to for climate reseachers at Norwegian Meteorological Institute to use AeroTools, by making the conversion between their modeldata files and Aerocom3 data. 

## Installation
To install, use pip
```
pip install git+https://github.com/metno/noresm-aerocom-converter.git
```
this will install NAC as a command line tool

## Usage
Use `nac <command> --help` to view the usage of the two commands.

NAC is a command line tool, with two commands `convert` and `from-file`. We recommend using `from-file` as it easier to use, and reproduce results. The difference is that when using `convert` the arguments and options are given in the command line, while in `from-file` only a path to a *yaml* file is given, where the aruguments for the conversion is stored.

With `convert`
```
nac convert [OPTIONS] INPUTDIR OUTPUTDIR EXPERIMENT FULLNAME BASEYEAR YEARS... LL 
```

and with `from-file`
```
nac from-file PATH  
```

### Conversion from File
The yaml file given to NAC must have the following fields

```
inputdir: <path of noresm data>
outputdir: <path to output  folder>
experiment: <name of experiment>
fullname: <full name of experiment, will be used for name of resulting files>
baseyear: <reference date. If years below is absolute (e.g. 2005), then use 0 here>
ll: <int, Vertical Level (used for some conversions)>
years: 
  - <year 1>
  - <year 2>
  - ...
variables:
  - <var1 (aercom3 variable)>
  - <var2 (aercom3 variable)>
  - ...
dry_run: <bool, if true, then all conversions will be done, but NAC will not save the results>
```

Not that NAC looks for the modeldata files with name `<inputdir>/atm/hist/<experiment>.cam.h0.<year>-<month>.nc`, so choose *experiment* and *inputdir* with this in mind.


## Formulas For Conversion
The conversion between NorESM variables and Aerocom3 variables follows formulas defined in [conversion.yaml](noresm_aerocom_converter/conversions.yaml). 

The formulas tell xarray how to do the conversion. A typical formula uses the names `x.<NORESM_NAME>` for NorESM variables. The `x.` is not found in NorESM data, but is used as a indetification marker of NorESM variables by the converter.

In some formulas `{<name>}` are used. This is for formatting during runtime, and is filled with constants defined in the program. `{LL}` is spesial, as it is swapped by the *ll* (Vertical Level) defined in the yaml file above.

As of now, to add custom formulas, you either have to clone and change, contact the developer or make a PR/issue. The possibility of personal, custom formula yamls are planned.


## COPYRIGHT

Copyright (C) 2023 Daniel Heinesen, Norwegian Meteorological Institute

This library is free software; you can redistribute it and/or
modify it under the terms of the GNU Lesser General Public
License as published by the Free Software Foundation; either
version 2.1 of the License, or (at your option) any later version.

This library is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
Lesser General Public License for more details.




