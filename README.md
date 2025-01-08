# Python Active Tigger client

Python wrapper to use ActiveTigger API

**Careful : This client is still under development and not all endpoints are implemented.**

## Installation

You need Python 3.11 or higher to use this package.

```bash
git clone https://github.com/emilienschultz/activetigger-client.git
```

And install requirements

```bash
cd activetigger-client
pip install -r requirements.txt
```

## Usage

You need the end-point url and a valid account/password to use this package.

You can create a YAML file `config.yaml` with the following content:

```yaml
url: https://your-endpoint-url
username: your-username
password: your-password
```

You can have an example of use in the notebook `Test client.ipynb`