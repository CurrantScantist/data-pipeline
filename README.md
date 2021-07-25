# data-pipeline
Data pipeline for the FIT4002 Full-Year-Project completed by Team 02 for Scantist.
This repository contains the data pipeline responsible for populating the database. It combines data from the scantist tools (Scantist SCA, Archtimize, and APIFuzzer) and data retrieved from the github API and stackshare API. The pipeline is built with the dagster framework (https://dagster.io/), their documentation can be found at https://docs.dagster.io/getting-started

## Setup

First make sure you have a virtual environment setup and activated.
Then run the following command:
```
python install -r requirements.txt
```

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
