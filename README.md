# data-pipeline &middot; [![codecov](https://codecov.io/gh/CurrantScantist/data-pipeline/branch/main/graph/badge.svg?token=MA5TKV9W4A)](https://codecov.io/gh/CurrantScantist/data-pipeline)
Data pipeline for the FIT4002 Full-Year-Project completed by Team 02 for Scantist.
This repository contains the data pipeline responsible for populating the database. It combines data from the scantist tools (Scantist SCA, Archtimize, and APIFuzzer) and data retrieved from the github API and stackshare API. The pipeline is built with the dagster framework (https://dagster.io/), their documentation can be found at https://docs.dagster.io/getting-started

## Setup

First make sure you have a virtual environment setup and activated.
Then run the following command:
```
python install -r requirements.txt
```
Also you will need to create a file named **secrets.py** which contains the necessary
access tokens for the database and APIs.

## Usage

### pipeline.py
To open the dagit web server run the following command in terminal:
```
dagit -f pipeline.py
```
A new web page should open with the dagit UI.

### pipeline_draft.py
This file contains the basic functionality of the data pipeline without typechecking, logs, UI, etc.
To run the pipeline_draft.py file, simply run it like any regular python file using either the terminal
or an IDE.
```
python pipeline_draft.py
```

### LOC_per_release.py
This is the newest addition to the repository. It contains the necessary functions for a pipeline which
calculates statistics about the LOC of a github repository. It calculates statistics for each release retrieved
from the github REST API for a particular repository and it pushes the data to the 'releases' collection on mongodb.

**Note:** In order for the LOC statistics to be calculated you must have 'cloc' installed on your system and it must
be accessible from the terminal by running the ```cloc``` command.

Open the CLI for this pipeline by running it from the terminal
```shell
python LOC_per_release.py
```

