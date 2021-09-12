from pipeline.pipeline import process_repository
import os

if __name__ == '__main__':
    # repo_input = input("Please enter a repository (eg, 'facebook/react'): ")
    # process_repository(repo_input)

    CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

    with open(os.path.join(CURRENT_DIR, 'input.txt'), 'r') as input_file:
        for line in input_file:
            process_repository(line.strip())
