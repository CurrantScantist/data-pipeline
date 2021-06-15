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
import requests
from dagster import pipeline, solid, Nothing, InputDefinition, OutputDefinition, List, String, Tuple, Int, \
    ModeDefinition, IOManager, io_manager
from dagster.experimental import DynamicOutput, DynamicOutputDefinition
import os

# class MyIOManager(IOManager):
#     def handle_output(self, context, obj):
#         pass

#     def load_input(self, context):
#         return ""


# @io_manager
# def my_io_manager(init_context):
#     return MyIOManager()


@solid(output_defs=[DynamicOutputDefinition(dagster_type=String)])
def get_repos(context):
    # path = context.solid_config["path"]
    dirname, _, filenames = next(os.walk("./"))
    for file in filenames:
        yield DynamicOutput(
            value=os.path.join(dirname, file),
            # create a mapping key from the file name
            mapping_key=file.replace(".", "_").replace("-", "_"),
        )


@solid(input_defs=[InputDefinition(name="repo", dagster_type=String)],
       output_defs=[OutputDefinition(dagster_type=String)])
async def metadata_retriever(context, repo):
    return ""


@solid(input_defs=[InputDefinition(name="repo", dagster_type=String)],
       output_defs=[OutputDefinition(dagster_type=String)])
async def popularity_retriever(context, repo):
    return ""


@solid(input_defs=[InputDefinition(name="repo", dagster_type=String)],
       output_defs=[OutputDefinition(dagster_type=String)])
async def scantist_SCA_retriever(context, repo):
    return ""


@solid(input_defs=[InputDefinition(name="repo", dagster_type=String)],
       output_defs=[OutputDefinition(dagster_type=String)])
async def archtimize_retriever(context, repo):
    return ""


@solid(input_defs=[
    InputDefinition(name="m", dagster_type=List[String]),
                   InputDefinition(name="c", dagster_type=List[String]),
                   InputDefinition(name="s", dagster_type=List[String]),
                   InputDefinition(name="a", dagster_type=List[String])],

       output_defs=[DynamicOutputDefinition(dagster_type=String)])
def collator(context, m, c, s, a):
    for repo_index in range(len(m)):
        yield DynamicOutput(
            value="",
            # create a mapping key from the file name
            mapping_key="collated_data_" + str(repo_index),
        )


@solid(input_defs=[InputDefinition(name="string", dagster_type=String)],
       output_defs=[OutputDefinition(dagster_type=String)])
def storer(context, string):
    return ""


# def multi(string):
#     data = [metadata_retriever(string), popularity_retriever(string), scantist_SCA_retriever(string), archtimize_retriever(string)]
#     data = collator(data)
#     storer(data)


# @pipeline(mode_defs=[ModeDefinition(resource_defs={"my_io_manager_key": my_io_manager})])
@pipeline
def data_pipeline():
    # repos = get_repos().map(multi)
    repos = get_repos()
    metadata = repos.map(metadata_retriever).collect()
    popularity = repos.map(popularity_retriever).collect()
    sca = repos.map(scantist_SCA_retriever).collect()
    archtimize = repos.map(archtimize_retriever).collect()

    data = collator(m=metadata, c=popularity, s=sca, a=archtimize)
    data.map(storer)

    # repos = get_repos().map(metadata_retriever).map(popularity_retriever).map(scantist_SCA_retriever).map(archtimize_retriever)


# @solid(output_defs=[OutputDefinition(io_manager_key="my_io_manager_key")])
# def my_solid(_):
#     return do_stuff()
