"""
Data pipeline for FIT4002 FYP

This pipeline retrieves all necessary data for a single repository, collates this data, and adds it to our mongoDB
database.

To run:
make sure dependencies are installed first, then run in the Backend/Dagster directory:
dagit -f pipeline.py

Author: Jack Whelan
Created on: 10/06/21
Last updated: 15/06/21
"""
import json
import bs4
from dagster.core.definitions import repository
import requests
from dagster import pipeline, solid, Nothing, InputDefinition, OutputDefinition, List, String, Tuple, Int, \
    ModeDefinition, IOManager, io_manager
from dagster.experimental import DynamicOutput, DynamicOutputDefinition
import os

from dagster_types import Repository, Metadata

# class MyIOManager(IOManager):
#     def handle_output(self, context, obj):
#         pass

#     def load_input(self, context):
#         return ""


# @io_manager
# def my_io_manager(init_context):
#     return MyIOManager()


@solid(output_defs=[DynamicOutputDefinition(dagster_type=Repository)])
def get_repos(context):
    # path = context.solid_config["path"]
    dirname, _, filenames = next(os.walk("../../"))
    for file in filenames:
        yield DynamicOutput(
            value=os.path.join(dirname, file),
            # create a mapping key from the file name
            mapping_key=file.replace(".", "_").replace("-", "_"),
        )


@solid(input_defs=[InputDefinition(name="repo", dagster_type=Repository)],
       output_defs=[OutputDefinition(dagster_type=Metadata)])
async def metadata_retriever(context, repo):
    metadata = {
        "projectUrl": "test/test",
        "versionNo": "1.0",
        "versionLastUpdatedDate": "1/1/1",
        "versionLastCVEDate": "1/1/1",
        "versionPackageManager": "npm",
        "versionLanguages": "",
        "versionLinesOfCode": 10,
        "versionSize": 10,
        "versionNumberOfCommits": 10
    }

    return metadata


@solid(input_defs=[InputDefinition(name="repo", dagster_type=Repository)],
       output_defs=[OutputDefinition(dagster_type=String)])
async def popularity_retriever(context, repo):
    return ""


@solid(input_defs=[InputDefinition(name="repo", dagster_type=Repository)],
       output_defs=[OutputDefinition(dagster_type=String)])
async def scantist_SCA_retriever(context, repo):
    return ""


@solid(input_defs=[InputDefinition(name="repo", dagster_type=Repository)],
       output_defs=[OutputDefinition(dagster_type=String)])
async def archtimize_retriever(context, repo):
    return ""


@solid(input_defs=[
    InputDefinition(name="metadata", dagster_type=List[Metadata]),
    InputDefinition(name="popularity", dagster_type=List[String]),
    InputDefinition(name="sca", dagster_type=List[String]),
    InputDefinition(name="archtimize", dagster_type=List[String])],

    output_defs=[DynamicOutputDefinition(dagster_type=String)])
def collator(context, metadata, popularity, sca, archtimize):
    for repo_index in range(len(metadata)):
        yield DynamicOutput(
            value="",
            # create a mapping key from the file name
            mapping_key="collated_data_" + str(repo_index),
        )


@solid(input_defs=[InputDefinition(name="string", dagster_type=String)],
       output_defs=[OutputDefinition(dagster_type=String)])
def storer(context, string):
    return ""


# @pipeline(mode_defs=[ModeDefinition(resource_defs={"my_io_manager_key": my_io_manager})])
@pipeline
def data_pipeline():
    # repos = get_repos().map(multi)
    repos = get_repos()
    metadata = repos.map(metadata_retriever).collect()
    popularity = repos.map(popularity_retriever).collect()
    sca = repos.map(scantist_SCA_retriever).collect()
    archtimize = repos.map(archtimize_retriever).collect()

    data = collator(metadata, popularity, sca, archtimize)
    data.map(storer)

    # repos = get_repos().map(metadata_retriever).map(popularity_retriever).map(scantist_SCA_retriever).map(archtimize_retriever)

