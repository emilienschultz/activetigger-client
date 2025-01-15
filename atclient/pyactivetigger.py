import io
import json
from pathlib import Path
from typing import List

import pandas as pd
import requests
import yaml
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


class AtApi:
    def __init__(self, url: str = None, config: str = None):
        """
        Initialize the client
        """
        self.headers = None
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
        response = requests.post(
            f"{self.url}/token",
            data={"username": username, "password": password},
            verify=False,
        )
        token_data = response.json()
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
        col_label: str = None,
        n_train: int = 500,
        n_test: int = 0,
        filename: str = "data",
        language: str = "fr",
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
        if col_label and col_label not in data.columns:
            raise Exception(f"Column {col_label} not found in data")

        # convert the data
        csv_string = data.to_csv(index=False)

        # build payload
        form = {
            "project_name": project_name,
            "col_id": col_id,
            "cols_text": cols_text,
            "col_label": col_label,
            "filename": filename,
            "cols_context": cols_context,
            "language": language,
            "n_train": n_train,
            "n_test": n_test,
            "csv": csv_string,
        }

        r = requests.post(
            f"{self.url}/projects/new", json=form, headers=self.headers, verify=False
        )
        print(r.content)

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
        self, project_slug: str, scheme: str, dataset: str = "train"
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
            return pd.read_csv(csv_io)
        except Exception as e:
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
                "kind": None,
                "labels": None,
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
