import io
import json
import os
from pathlib import Path
from typing import List

import pandas as pd  # type: ignore[import]
import requests  # type: ignore[import]
import yaml  # type: ignore[import]
from requests.packages.urllib3.exceptions import (  # type: ignore[import]
    InsecureRequestWarning,
)

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


class AtApi:
    def __init__(self, url: str | None = None, config: str | None = None):
        """
        Initialize the client
        """
        self.headers: dict[str, str] | None = None
        if config:
            if not Path(config).is_file():
                raise Exception("Config file does not exist")
            with open(Path(config), "r") as stream:
                config_data = yaml.load(stream, Loader=yaml.FullLoader)
            if "url" not in config_data:
                raise Exception("Url not found in config file")
            self.url = config_data.get("url")
            if "username" in config_data and "password" in config_data:
                self.connect(config_data.get("username"), config_data.get("password"))
        else:
            if not url:
                raise Exception("Url not provided")
            self.url = url

    def connect(self, username: str, password: str):
        """
        Get token access with username/password
        """
        try:
            response = requests.post(
                f"{self.url}/token",
                data={"username": username, "password": password},
                verify=False,
            )
            token_data = response.json()
        except Exception as e:
            print(e)
            print("Error to connect to endpoint")
            return
        access_token = token_data.get("access_token")
        if access_token:
            self.headers = {
                "Authorization": f"Bearer {access_token}",
                "username": username,
            }
            print("Token received")

        else:
            print("Error in token request")

    def get_project_state(self, project_slug: str):
        """
        Get project state
        """
        if not self.headers:
            raise Exception("No token found")
        r = requests.get(
            f"{self.url}/projects/{project_slug}", headers=self.headers, verify=False
        )
        return r.json()

    def get_projects(self):
        """
        Get projects
        """
        if not self.headers:
            raise Exception("No token found")
        r = requests.get(f"{self.url}/projects", headers=self.headers, verify=False)
        try:
            return r.json()["projects"]
        except Exception as e:
            print(e)
            return None

    def get_projects_slugs(self):
        """
        Get projects slugs
        """
        if not self.headers:
            raise Exception("No token found")
        r = requests.get(f"{self.url}/projects", headers=self.headers, verify=False)
        try:
            return [i["parameters"]["project_slug"] for i in r.json()["projects"]]
        except Exception as e:
            print(e)
            return None

    def add_project(
        self,
        project_name: str,
        data: pd.DataFrame,
        col_id: str,
        cols_text: List[str],
        cols_context: List[str] = [],
        cols_label: list | None = None,
        n_train: int = 500,
        n_test: int = 0,
        filename: str = "data.csv",
        language: str = "fr",
        random_selection: bool = True,
    ):
        """
        Create a new project

        Args:
            project_name: name of the project
            data: data to use as a Pandas DataFrame
            col_id: column id
            cols_text: list of text columns
            cols_context: list of context columns
            col_label: label column
        """

        if not self.headers:
            raise Exception("No token found")

        # test if the elements exist
        if col_id not in data.columns:
            raise Exception(f"Column {col_id} not found in data")
        for col_text in cols_text:
            if col_text not in data.columns:
                raise Exception(f"Column {col_text} not found in data")
        for col_context in cols_context:
            if col_context not in data.columns:
                raise Exception(f"Column {col_context} not found in data")
        if cols_label is not None:
            for col_label in cols_label:
                if col_label not in data.columns:
                    raise Exception(f"Column {cols_label} not found in data")

        # send the file
        csv_string = data.to_csv(index=False)
        r = requests.post(
            f"{self.url}/files/add/project",
            params={"project_name": project_name},
            files={"file": (filename, csv_string)},
            verify=False,
            headers=self.headers,
        )

        print(r.json())

        # create the project
        form = {
            "project_name": project_name,
            "col_id": col_id,
            "cols_text": cols_text,
            "cols_label": cols_label,
            "filename": filename,
            "cols_context": cols_context,
            "language": language,
            "n_train": n_train,
            "n_test": n_test,
            "random_selection": random_selection,
        }

        r = requests.post(
            f"{self.url}/projects/new", json=form, headers=self.headers, verify=False
        )
        return r.json()

    def delete_project(self, project_slug: str):
        """
        Delete a project
        """
        if not self.headers:
            raise Exception("No token found")

        r = requests.post(
            f"{self.url}/projects/delete",
            headers=self.headers,
            verify=False,
            params={"project_slug": project_slug},
        )

        if r.content == b"null":
            print("Project deleted")
        else:
            print(r.content)

    def get_users(self):
        """
        Get users
        """
        if not self.headers:
            raise Exception("No token found")
        r = requests.get(f"{self.url}/users", headers=self.headers, verify=False)
        return r.json()["users"]

    def add_user(
        self, username: str, password: str, mail: str, status: str = "manager"
    ):
        """
        Create a new user
        """

        if not self.headers:
            raise Exception("No token found")

        query = {
            "username_to_create": username,
            "password": password,
            "status": status,
            "mail": mail,
        }
        r = requests.post(
            f"{self.url}/users/create", params=query, headers=self.headers, verify=False
        )

        if r.content == b"null":
            print("User created")
        else:
            print(r.content)

    def delete_user(self, username: str) -> None:
        """
        Delete a user
        """
        if not self.headers:
            raise Exception("No token found")
        r = requests.post(
            f"{self.url}/users/delete",
            headers=self.headers,
            verify=False,
            params={"user_to_delete": username},
        )
        if r.content == b"null":
            print("User deleted")
        else:
            print(r.content)

    def get_annotations_data(
        self,
        project_slug: str,
        scheme: str,
        dataset: str = "train",
        verbose: bool = False,
    ):
        """
        Get current annotations for a projet/scheme
        """
        if not self.headers:
            raise Exception("No token found")
        r = requests.get(
            f"{self.url}/export/data",
            params={
                "project_slug": project_slug,
                "scheme": scheme,
                "dataset": dataset,
                "format": "csv",
            },
            headers=self.headers,
            verify=False,
        )
        try:
            csv_decoded = r.content.decode("utf-8")
            csv_io = io.StringIO(csv_decoded)
            t = pd.read_csv(csv_io)
            if len(t) == 0:
                raise Exception(f"No {dataset} found for {project_slug} {scheme}")
            return t
        except Exception as e:
            if verbose:
                print(e)
            return None

    def add_auth_user_project(
        self, username: str, project_slug: str, auth: str = "manager"
    ):
        """
        Add a user to a project
        """
        if not self.headers:
            raise Exception("No token found")
        r = requests.post(
            f"{self.url}/users/auth/add",
            headers=self.headers,
            verify=False,
            params={"project_slug": project_slug, "username": username, "status": auth},
        )
        if r.content == b"null":
            print("Auth added to user")
        else:
            print(r.content)

    def delete_auth_user_project(self, username: str, project_slug: str):
        """
        Delete a user from a project
        """
        if not self.headers:
            raise Exception("No token found")
        r = requests.post(
            f"{self.url}/users/auth/delete",
            headers=self.headers,
            verify=False,
            params={"project_slug": project_slug, "username": username},
        )
        if r.content == b"null":
            print("Auth deleted for user")
        else:
            print(r.content)

    def get_features(self, project_slug: str):
        """
        Get features of the project
        """
        if not self.headers:
            raise Exception("No token found")
        r = requests.get(
            f"{self.url}/features/available",
            headers=self.headers,
            verify=False,
            params={"project_slug": project_slug},
        )
        try:
            return json.loads(r.content)
        except Exception as e:
            print(e)
            return None

    def add_feature(
        self,
        project_slug: str,
        feature_name: str,
        feature_type: str,
        feature_parameters: dict = {},
    ):
        """
        Train a feature
        """
        if not self.headers:
            raise Exception("No token found")
        r = requests.post(
            f"{self.url}/features/add",
            headers=self.headers,
            verify=False,
            params={"project_slug": project_slug},
            json={
                "name": feature_name,
                "type": feature_type,
                "parameters": feature_parameters,
            },
        )
        if r.content == b"null":
            print("Feature in training")
        else:
            print(r.content)

    def get_features_data(
        self, project_slug: str, features: list[str], format: str = "csv"
    ):
        """
        Get features from a project
        """
        if not self.headers:
            raise Exception("No token found")
        r = requests.get(
            f"{self.url}/export/features",
            params={
                "project_slug": project_slug,
                "features": features,
                "format": format,
            },
            headers=self.headers,
            verify=False,
        )
        try:
            csv_decoded = r.content.decode("utf-8")
            csv_io = io.StringIO(csv_decoded)
            return pd.read_csv(csv_io)
        except Exception as e:
            print(e)
            return None

    def get_schemes(self, project_slug: str):
        """
        Get schemes of a project
        """
        if not self.headers:
            raise Exception("No token found")
        r = self.get_project_state(project_slug)
        if "schemes" in r:
            return r["schemes"]["available"]
        else:
            print("Error, no schemes field")
            return None

    def add_scheme_to_project(
        self,
        project_slug: str,
        scheme: str,
        labels: str | None = None,
        kind: str = "multiclass",
    ):
        """
        Add a scheme to a project
        """
        if not self.headers:
            raise Exception("No token found")
        r = requests.post(
            f"{self.url}/schemes/add",
            headers=self.headers,
            verify=False,
            params={"project_slug": project_slug},
            json={
                "project_slug": project_slug,
                "name": scheme,
                "kind": kind,
                "labels": labels,
            },
        )
        if r.content == b"null":
            print("Scheme added to project")
        else:
            print(r.content)

    def delete_scheme_from_project(self, project_slug: str, scheme: str):
        """
        Delete a scheme from a project
        """
        """
        Add a scheme to a project
        """
        if not self.headers:
            raise Exception("No token found")
        r = requests.post(
            f"{self.url}/schemes/delete",
            headers=self.headers,
            params={"project_slug": project_slug},
            verify=False,
            json={
                "project_slug": project_slug,
                "name": scheme,
                "kind": "",
                "labels": [],
            },
        )
        if r.content == b"null":
            print("Scheme deleted from project")
        else:
            print(r.content)

    def add_label_to_scheme(self, project_slug: str, scheme: str, label: str):
        """
        Add a label to a scheme
        """
        if not self.headers:
            raise Exception("No token found")
        r = requests.post(
            f"{self.url}/schemes/label/add",
            headers=self.headers,
            verify=False,
            params={"project_slug": project_slug, "scheme": scheme, "label": label},
        )
        if r.content == b"null":
            print("Label added to scheme")
        else:
            print(r.content)

    def delete_label_from_scheme(self, project_slug: str, scheme: str, label: str):
        """
        Delete a label from a scheme
        """
        if not self.headers:
            raise Exception("No token found")
        r = requests.post(
            f"{self.url}/schemes/label/delete",
            headers=self.headers,
            verify=False,
            params={"project_slug": project_slug, "scheme": scheme, "label": label},
        )
        if r.content == b"null":
            print("Label deleted from scheme")
        else:
            print(r.content)

    def download_raw_dataset(self, project_slug: str, folder: str = "./"):
        """
        Download raw dataset
        """
        if not self.headers:
            raise Exception("No token found")
        r = requests.get(
            f"{self.url}/export/raw",
            headers=self.headers,
            verify=False,
            params={"project_slug": project_slug},
        )
        try:
            r = r.json()
            response = requests.get(
                f"{self.url}/{r['path']}", stream=True, verify=False
            )
            if response.status_code == 200:
                with open(f"{folder}/{r['name']}", "wb") as out_file:
                    for chunk in response.iter_content(chunk_size=8192):
                        out_file.write(chunk)
            else:
                print("Error in downloading file")
        except Exception as e:
            print(e)

    def export_project(
        self, project_slug: str, path: str = "./exports", raw_datasets: bool = False
    ):
        """
        Save a project
        for each scheme :
            - save train/test annotations
        """
        if not self.headers:
            raise Exception("No token found")

        print(f"Starting the export of project {project_slug}")

        # create folder
        if Path(f"{path}/{project_slug}").exists():
            print(
                "This project seems already be saved, check or delete the previous version"
            )
            return None

        # create the folder
        os.makedirs(f"{path}/{project_slug}")
        path_project = f"{path}/{project_slug}"

        # get the state of the project to save it
        state = self.get_project_state(project_slug)
        with open(f"{path_project}/{project_slug}.json", "w") as f:
            json.dump(state, f)

        # get schemes annotation for each scheme
        schemes = self.get_schemes(project_slug)
        for scheme in schemes:
            t = self.get_annotations_data(project_slug, scheme, "train")
            if t is not None:
                t.to_csv(f"{path_project}/annotations-scheme-{scheme}-train.csv")
            t = self.get_annotations_data(project_slug, scheme, "test")
            if t is not None:
                t.to_csv(f"{path_project}/annotations-scheme-{scheme}-test.csv")

        print(f"Project {project_slug} saved with {len(schemes)} schemes")

        # if requested, export raw dataset
        if raw_datasets:
            self.download_raw_dataset(project_slug, path_project)
            print("Raw dataset downloaded")

        return None

    def export_all(self, path: str = "./exports", raw_datasets: bool = False):
        """
        Save all the data
        """
        projects = self.get_projects_slugs()
        print(projects)
        for project in projects:
            self.export_project(project, path, raw_datasets)

    def get_models(self, project_slug: str) -> dict:
        """
        Get model state
        """
        r = self.get_project_state(project_slug)
        return {
            "available": r["bertmodels"]["available"],
            "training": r["bertmodels"]["training"],
        }

    def stop_finetune_model(self, project_slug: str, specific_user: str | None = None):
        """
        Stop training a model
        """
        if not self.headers:
            raise Exception("No token found")
        r = requests.post(
            f"{self.url}/models/bert/stop",
            headers=self.headers,
            verify=False,
            params={"project_slug": project_slug, "specific_user": specific_user},
        )
        if r.content == b"null":
            print("Model stopped")
        else:
            print(r.content)

    def start_finetune_model(
        self,
        project_slug: str,
        scheme: str,
        name: str,
        base_model: str,
        params: dict | None = None,
        test_size: float = 0.2,
        dichotomize: str | None = None,
        class_min_freq: int = 1,
        class_balance: bool = False,
    ):
        """
        Start training a model
        """
        if not self.headers:
            raise Exception("No token found")

        if params is None:
            params = {
                "batchsize": 4,
                "gradacc": 1,
                "epochs": 3,
                "lrate": 5e-05,
                "wdecay": 0.01,
                "best": True,
                "eval": 10,
                "gpu": True,
                "adapt": True,
            }

        payload = {
            "project_slug": project_slug,
            "scheme": scheme,
            "name": name,
            "base_model": base_model,
            "params": params,
            "test_size": test_size,
            "dichotomize": dichotomize,
            "class_min_freq": class_min_freq,
            "class_balance": class_balance,
        }

        r = requests.post(
            f"{self.url}/models/bert/train",
            headers=self.headers,
            verify=False,
            params={"project_slug": project_slug},
            json=payload,
        )

        if r.content == b"null":
            print("Model in training")
        else:
            print(r.content)
