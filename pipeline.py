"""
Data pipeline for FIT4002 FYP

This pipeline retrieves all necessary data for a single repository, collates this data, and adds it to our mongoDB
database.

To run:
make sure dependencies are installed first, then run in the Backend/Dagster directory:
dagit -f pipeline.py

Author: Jack Whelan
Created on: 10/06/21
Last updated: 10/06/21
"""
import json
import bs4
import requests
from dagster import pipeline, solid, Nothing, InputDefinition, OutputDefinition, List, String, Tuple, Int


@solid(output_defs=[OutputDefinition(dagster_type=String)])
def get_repo(context):
    return ""


@solid(input_defs=[InputDefinition(name="repo", dagster_type=String)],
       output_defs=[OutputDefinition(dagster_type=String)])
def metadata_retriever(context, repo):
    return ""


@solid(input_defs=[InputDefinition(name="repo", dagster_type=String)],
       output_defs=[OutputDefinition(dagster_type=String)])
def community_retriever(context, repo):
    return ""


@solid(input_defs=[InputDefinition(name="repo", dagster_type=String)],
       output_defs=[OutputDefinition(dagster_type=String)])
def scantist_SCA_retriever(context, repo):
    return ""


@solid(input_defs=[InputDefinition(name="repo", dagster_type=String)],
       output_defs=[OutputDefinition(dagster_type=String)])
def archtimize_retriever(context, repo):
    return ""


@solid(input_defs=[InputDefinition(name="strings", dagster_type=List[String])],
       output_defs=[OutputDefinition(dagster_type=String)])
def collator(context, strings):
    return ""


@solid(input_defs=[InputDefinition(name="string", dagster_type=String)],
       output_defs=[OutputDefinition(dagster_type=String)])
def storer(context, string):
    return ""


@pipeline
def spike_pipeline():
    repo = get_repo()
    data = [metadata_retriever(repo), community_retriever(repo), scantist_SCA_retriever(repo),
            archtimize_retriever(repo)]
    collated = collator(data)
    storer(collated)
