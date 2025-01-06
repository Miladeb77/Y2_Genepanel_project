# Installation

These instructions will allow you to install the package and accompanying databases on Linux. 
For any other systems, or if you cannot install the databases, we recommend installing via [docker](DOCKER.md).

## Pre-requisites
Installation requires [PanelGeneMapper](https://github.com/Miladeb77/Y2_Genepanel_project)
## Installing

Download the git repo
```bash
$ git clone https://github.com/Miladeb77/Y2_Genepanel_project
$ cd Y2_Genepanel_project
```

Create a virtual environment - recommended
```bash
$ conda env create -f environment.yml
$ conda activate PanelApp_project
```

See the [PanelGeneMapper](https://github.com/Miladeb77/Y2_Genepanel_project) Installation and README documentations to install the panelapp databases, integrate patient databases and set up configurations. You will need to run build_panelapp_database.py and build_patient_database.py to set up databases for the software.
