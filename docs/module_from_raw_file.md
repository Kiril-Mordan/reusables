The most straight forward way to use the code without a need to either make a package or manually coping is to import from repository.

First define funtion for importing and then use it to import data with url to a particular point.

``` python
import requests
import importlib.util
import sys

def import_module_from_url(github_raw_url : str,
                           module_name : str) -> None:

    try:
        # Download the raw file
        response = requests.get(github_raw_url)
        response.raise_for_status()

        # Create a temporary module
        spec = importlib.util.spec_from_loader(module_name, loader=None)
        module = importlib.util.module_from_spec(spec)

        # Load the code into the module
        exec(response.text, module.__dict__)

        # Add the module to the current script's namespace
        sys.modules[module_name] = module

    except requests.exceptions.RequestException as e:
        print(f"Failed to download module from GitHub: {e}")
```

Find raw url to the python module and follow the example:

``` python
url = 'https://raw.githubusercontent.com/Kiril-Mordan/reusables/main/python_modules/google_drive_support.py'

import_module_from_url(github_raw_url=url,
                       module_name='google_drive_support')

from google_drive_support import get_google_drive_file_id, download_file, service_account, build
```