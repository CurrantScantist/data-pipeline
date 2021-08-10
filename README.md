# data-pipeline &middot; [![codecov](https://codecov.io/gh/CurrantScantist/data-pipeline/branch/main/graph/badge.svg?token=MA5TKV9W4A)](https://codecov.io/gh/CurrantScantist/data-pipeline) [![CodeFactor](https://www.codefactor.io/repository/github/currantscantist/data-pipeline/badge?s=82506a57146579e1e65876e36dee944c5b8649ff)](https://www.codefactor.io/repository/github/currantscantist/data-pipeline)
Data pipeline for the FIT4002 Full-Year-Project completed by Team 02 for Scantist.
This repository contains the data pipeline responsible for populating the database. It combines data from the scantist tools (Scantist SCA, Archtimize, and APIFuzzer) and data retrieved from the github API and stackshare API. The pipeline is built with the dagster framework (https://dagster.io/), their documentation can be found at https://docs.dagster.io/getting-started

## Setup

First make sure you have a virtual environment setup and activated.
Then run the following command:
```
pip install -r requirements.txt
```
Also you will need to create a file for environment variables named **.env** which contains the necessary
access tokens for the database and APIs.

## Usage

### dagster_pipeline.py
To open the dagit web server run the following command in terminal:
```
dagit -f ./src/pipeline/dagster_pipeline.py
```
A new web page should open with the dagit UI.

### main.py
This is the newest addition to the repository. It contains the necessary functions for a pipeline which
calculates statistics about the LOC of a github repository. It calculates statistics for each tag in the
particular repository, and then it pushes the data to the 'releases' collection on mongodb.

**Note:** In order for the LOC statistics to be calculated you must have 'cloc' installed on your system and it must
be accessible from the terminal by running the ```cloc``` command. The tool can be found here https://github.com/AlDanial/cloc

Open the CLI for this pipeline by running it from the terminal
```shell
python ./src/main.py
```

## Testing
To run the unit tests for the pipeline functions. Make sure pytest is installed and simply run the command `pytest`
in the root directory.
Code coverage html reports can be found as artefacts in the github actions workflows

