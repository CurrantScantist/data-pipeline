# data-pipeline &middot; [![codecov](https://codecov.io/gh/CurrantScantist/data-pipeline/branch/main/graph/badge.svg?token=MA5TKV9W4A)](https://codecov.io/gh/CurrantScantist/data-pipeline) [![CodeFactor](https://www.codefactor.io/repository/github/currantscantist/data-pipeline/badge?s=82506a57146579e1e65876e36dee944c5b8649ff)](https://www.codefactor.io/repository/github/currantscantist/data-pipeline)
Data pipeline for the FIT4002 Full-Year-Project completed by Team 02 for Scantist.
This repository contains the data pipeline responsible for populating the database. It combines data from scantist SCA (scantist.io), github, and cloc (https://github.com/AlDanial/cloc).

## Setup

### python virtual environment
First make sure you have a virtual environment setup and activated.
Then run the following command:
```shell
pip install -r requirements.txt
```

### environment variables (.env)
You will need to create a file for environment variables named **.env** in the repository directory which contains the necessary
access tokens for the database and APIs. It should have the variables shown in the code block below. Note: the optional github access tokens are
not necessary to run the pipeline successfully however, they are highly recommended in order to speed up the github issue and pull request retrieval since
this is what takes up most of the time of the pipeline.

```dotenv
# connection string for remote db
CONNECTION_STRING = "mongodb+srv://admin:..."

# Personal Access Token (PAT) for github API requests
ACCESS_TOKEN = "abcdedfgh47873891238" # this one is required for most github API interactions
ACCESS_TOKEN2 = "abcdedfgh47873891238" # optional
ACCESS_TOKEN3 = "abcdedfgh47873891238" # optional
ACCESS_TOKEN4 = "abcdedfgh47873891238" # optional
ACCESS_TOKEN5 = "abcdedfgh47873891238" # optional

# Access Token for Scantist SCA
SCANTISTTOKEN = "abcdedfgh47873891238"
```

### CLI dependencies
In order for the LOC statistics to be calculated you must have 'cloc' installed on your system and it must
be accessible from the terminal by running the ```cloc``` command. The tool can be found here https://github.com/AlDanial/cloc


## Usage

### Process repositories from a list

Edit the /src/input.txt file to contain the repositories you want to process as shown below.
```text
sveltejs/svelte
vuejs/vue
facebook/react
angular/angular
```
Then run the pipeline by typing the following into the terminal
```shell
python src/main.py
```

### Logging
By default, the pipeline logs to both the console and log files. The log folder structure is based on the time that the pipeline runs were started.
An example of the logging directory structure is below.
```
src/pipeline/logs
└───2021-10
│   └─── 2021-10-02T12-48-49
│       │   sveltejs-svelte.log
│       │   vuejs-vue.log
│       │   facebook-react [ERROR].log
│       │   angular-angular [ERROR].log
│       │   ...
```
**Note:** "[ERROR]" is appended to the log file name dynamically if an exception occurred while processing that particular repository.
If any exceptions occurred while processing a repository, the traceback information will be available in the relevant log file.

## Testing
To run the unit tests for the pipeline functions, make sure pytest is installed and simply run the command `pytest` (or `pytest -vv` for more verbose results)
in the root directory.
Code coverage html reports can be found as artefacts in the github actions workflows

