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

    def create_project(
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

    def delete_project(self, project_id: str):
        """
        Delete a project
        """
        if not self.headers:
            raise Exception("No token found")
        # TODO

    def create_user(
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
        print(r.content)

    def delete_user(self, username: str):
        """
        Delete a user
        """
        if not self.headers:
            raise Exception("No token found")
        # TODO

    def add_auth_user_project(self, username: str, project_id: str):
        """
        Add a user to a project
        """
        if not self.headers:
            raise Exception("No token found")
        # TODO

    def delete_auth_user_project(self, username: str, project_id: str):
        """
        Delete a user from a project
        """
        if not self.headers:
            raise Exception("No token found")
        # TODO
