# Test script for the API

General guidelines : 

- the client (in `../atclient` folder) is used to make tests for the API
- the `../atclient/automate.py` contains function to orchestrate automatic tests to avoid to duplicate code
- a file `config.yaml` contains the url and the root access
- data to use is in `../data/dataset.parquet`, with the `id` for index, the `text` for the text, and `label` for label.
- each script can be launched with the CLI

All scripts need to clean the API before finishing, destroying the elements created during the process.

## Is active

The script `test_api_activity.py` test if the API is up and working.

## Can create a project

The script `test_api_create_project.py` test if the client can create a project with the data in `data/dataset.parquet` and a trainset of 1000 elements.

## Can create users

The script `test_api_create_users.py` test if the client can create a user, grant and revoke project access, and clean up.

## Can train models

The script `test_api_train_models.py` test if the client can start and stop a BERT model training (camembert/camembert-base) on a project with forced labels.
