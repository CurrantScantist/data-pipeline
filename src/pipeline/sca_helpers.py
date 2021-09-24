import requests
from .exceptions import HTTPError
import subprocess
import json
import os
from tqdm import tqdm
import traceback


def download_scantist_bom_detector(repos_dir, url="https://scripts.scantist.com/scantist-bom-detect.jar"):
    """
    Downloads the scantist_bom_detector jar file necessary for running the Scantist SCA CLI.
    :param repos_dir: the path to the temporary folder that stores all of the cloned repositories
    :param url: the url of the scantist bom detector
    :return: A tuple where the first item is a boolean for whether the file was downloaded or not, and the second item
            is the path of the scantist bom detector file
    """
    file_name = url.split("/")[-1]
    file_path = os.path.join(repos_dir, file_name)
    # check if the file exists first
    if os.path.exists(file_path):
        return False, file_path

    r = requests.get(url)
    if r.status_code != 200:
        raise HTTPError(r.status_code)

    with open(file_path, 'wb') as output_file:
        output_file.write(r.content)

    return True, file_path


def call_scantist_sca(repo_path, bom_detector_path, server_url="http://119.8.181.73:8237/"):
    """
    Triggers a Scantist SCA scan via the CLI and returns the results as a tuple of two dictionaries
    :param server_url: the url of the Scantist server to upload the CLI scan to
    :param repo_path: the path of the repository
    :param bom_detector_path: the path of the scantist bom detector
    :return: a tuple of two dictionaries, the results generated by the Scantist SCA run, and the dependency tree data
    """
    p = subprocess.run(f"java -jar {bom_detector_path} -working_dir {repo_path} -download_report "
                       f"-serverUrl {server_url} --debug")
    if p.returncode != 0:
        raise SystemError(p.stderr)

    with open(os.path.join(repo_path, "Scantist-Reports.json"), 'r') as report_file:
        sca_report_data = json.loads(report_file.read())

    with open(os.path.join(repo_path, "dependency-tree.json"), 'r') as dep_file:
        dep_tree_data = json.loads(dep_file.read())

    return sca_report_data, dep_tree_data


def generate_node_link_data(dep_tree_data, report_data, max_level=10):
    """
    Generates the data format required to display a node link diagram using popular data visualisation libraries.
    The nodes represent dependencies of the project, links represent a dependency relationship, and the categories
    represent the licenses of the dependencies.
    :param dep_tree_data: the dependency tree data generated from the Scantist bom-detector.jar file
    :param report_data: the Scantist report data generated from a Scantist SCA scan.
    :param max_level: the maximum dependency depth to include in the data
    :return: the node link data
    """
    data = {
        "type": "force",
        "categories": [{"name": "test", "keyword": {}, "base": "test"}],
        "nodes": {},
        "links": []
    }
    licenses = report_data["results"]["licenses"]
    licenses = list(set(x["license_name"] if x["license_name"] is not None else "None" for x in licenses))

    if "None" in licenses:  # bringing the "None" license to the start so that it is the default value
        licenses.insert(0, licenses.pop(licenses.index("None")))

    data["categories"] = [{"name": x, "keyword": {}, "base": x} for x in licenses]

    licenses = dict(zip(licenses, list(range(len(licenses)))))

    def recurse(obj, parent=None):
        """
        Function to recursively loop through the dependency structure and find the nodes and links between nodes
        :param obj: the current object
        :param parent: the parent object (unless the current object is the root node)
        :return: None
        """
        nonlocal data
        if obj["level"] >= max_level:
            return

        # add the node to the data
        lib_id = 0
        lib_name = obj["artifact_id"].lower()
        if lib_name not in data["nodes"]:
            lib_id = len(data["nodes"].keys())
            data["nodes"][lib_name] = {
                "id": lib_id,
                "name": lib_name,
                "value": 1 if obj["type"] == "dependency" else 2,
                "category": 0
            }
        else:
            lib_id = data["nodes"][lib_name]["id"]
        # add the link to the data
        if parent is not None:
            data["links"].append({
                "source": data["nodes"][parent["artifact_id"].lower()]["id"],
                "target": lib_id
            })
        if "dependencies" in obj:
            for dep in obj["dependencies"]:
                recurse(dep, obj)

    recurse(dep_tree_data["projects"][0])

    # Updating the license information for each node
    for dep_license in report_data["results"]["licenses"]:
        license_name = dep_license["license_name"]
        if license_name is None:
            license_name = "None"

        if dep_license["library"] is None:
            continue
        if dep_license["library"] == "dummy-lib":
            continue

        license_index = licenses[license_name]
        library = dep_license["library"]
        data["nodes"][library]["category"] = license_index

    data["nodes"] = list(data["nodes"].values())

    return data


def push_scantist_sca_data_to_mongodb(repo_owner, repo_name, data, client):
    """
    Pushes the repository metadata to the mongoDB database
    :param repo_owner: the owner of the repository. Eg, 'facebook'
    :param repo_name: the name of the repository. Eg, 'react'
    :param data: the metadata for the repository (python dictionary)
    :param client: the MongoDB client
    :return: None
    """
    db = client['test_db']
    sca_collection = db['repositories']
    search_dict = {
        "name": repo_name,
        "owner": repo_owner,
    }
    sca_collection.update_one(search_dict, {'$set': data}, upsert=True)


def collect_scantist_sca_data(repos_dir, repo_path, repo_owner, repo_name, mongo_client, logger):
    """
    Main function for integrating the pipeline with the Scantist SCA CLI. This function downloads the Scantist
    bom-detector.jar file (if needed), triggers a CLI scan, reads the results, generates the data needed for a
    node-link diagram and then pushes the data to mongodb
    :param repos_dir: the directory of the repositories
    :param repo_path: the path of the specific repository
    :param repo_owner: the owner of the repository
    :param repo_name: the name of the repository
    :param mongo_client: the MongoClient object for PyMongo
    :param logger: The logger object to use for logging information
    :return: None
    """
    # downloading the scantist-bom-detector
    logger.info('checking if the scantist-bom-detector is already downloaded')
    did_download, bom_detector_path = download_scantist_bom_detector(repos_dir)
    if did_download:
        logger.info("Scantist_bom_detector downloaded successfully")
    else:
        logger.info("Scantist_bom_detector was found locally")

    logger.info("Triggering Scantist SCA scan")
    try:
        sca_report_data, dep_tree_data = call_scantist_sca(repo_path, bom_detector_path)

        logger.info("Generating node link data")
        node_link_data = generate_node_link_data(dep_tree_data, sca_report_data)

        data = {
            "num_vulnerabilities": len(sca_report_data["results"]["vulnerabilities"]),
            "num_components": len(sca_report_data["results"]["components"]),
            "vulnerability_breakdown": sca_report_data["results"]["issue_breakdown"],
            "nodelink_data": node_link_data
        }
        push_scantist_sca_data_to_mongodb(repo_owner, repo_name, data, mongo_client)

        # remove the generated files
        # os.remove(os.path.join(repo_path, "Scantist-Reports.json"))
        # os.remove(os.path.join(repo_path, "dependency-tree.json"))

    except Exception as e:
        traceback.print_exc()
