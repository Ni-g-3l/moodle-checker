# Moodle-checker

## Description 

This little script allow students of work and study program from University of Bordeaux to send their presence online.

## Requirements

* Python 3.8 or more
* Internet Connection

## Installation

### From Github

Download wheel file from [here](https://github.com/Ni-g-3l/moodle-checker/releases)

Then, open your terminal as administrator and run commands :

```bash
python -m pip install <path_to_your_wheel>
moodle_checker_install
``` 

### From Source 

* Install Poetry [[Install Guide](https://python-poetry.org/docs/#installation)]
* Clone this repository
* Install Dependances

Inside repository folder, launch this command.
```bash
poetry install
```
* Build Wheel

```bash
poetry build
```
* Install Wheel
```bash
python -m pip install <path_to_your_wheel>
moodle_checker_install
```

## Launch 

In order to send your presence online you need to run the command :

```bash
moodle_checker --user=<your moodle username> --password=<your moodle password>
```

## Licenses

------
"THE BEER-WARE LICENSE" (Revision 42):
<nig3lpro@gmail.com> wrote this file. As long as you retain this notice you
can do whatever you want with this stuff. If we meet some day, and you think
this stuff is worth it, you can buy me a beer in return.

-----