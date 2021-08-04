from pipeline.LOC_per_release import process_repository

if __name__ == '__main__':
    repo_input = input("Please enter a repository (eg, 'facebook/react'): ")
    process_repository(repo_input)
