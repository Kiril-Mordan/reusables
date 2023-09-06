# Reusables

Contains pieces of code that were generalized to a point where they can be reused in other projects, but due to their nature, do not deserve their own package.

## Usage

The most straight forward way to use the code without a need to either make a package or manually coping is to import from repository.

First define funtions for importing and then use it to import data with url to a particular point.

``` python
import requests
def import_module_from_url(url):
    exec(requests.get(url).text)
```

## Content:
 
[google_drive_support.py](python_modules/google_drive_support.py) - Google Drive API Utilities Module

This module provides a set of functions for interacting with the Google Drive API.
It allows you to authenticate with the API, upload, download, and manage files and folders in Google Drive.

