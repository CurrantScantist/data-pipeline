from pipeline.pipeline import process_repository, get_current_repo_names
import datetime
import os
import argparse
from dotenv import load_dotenv


if __name__ == '__main__':
    load_dotenv()
    parser = argparse.ArgumentParser(description="FIT4002 Team 02 Data Pipeline")

    """
    options:
     - input.txt file
     - single repository name
     - repositories currently in the db
     - limit the number of languages displayed?
     - change the colours?
     
    extra:
     - log directory
     - bool for whether to log to a file or not
     - bool for whether to override existing data in the database?
    """

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--repository', '-r', type=str, help="The repository written as '<owner>/<name>'")
    group.add_argument('--repo-list', '-i', type=argparse.FileType('r', encoding='utf-8'),
                       help="A text file containing a repository for each line in the form '<owner>/<name>'")
    group.add_argument('--current-repos', '-c', action='store_true',
                       help="Process the repositories currently stored in the database")
    parser.add_argument('--log-dir', '-l', type=str, help="The directory to create the log files")
    args = parser.parse_args()

    current_datetime = datetime.datetime.now()

    # process a single repository
    if args.repository is not None:
        process_repository(args.repository, current_datetime)

    # process repositories from a list in a text file
    elif args.repo_list is not None:
        for line in args.repo_list:
            process_repository(line.strip(), current_datetime)

    # process the repositories currently in the database
    elif args.current_repos:
        for repo_str in get_current_repo_names():
            process_repository(repo_str, current_datetime)
