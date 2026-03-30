"""
Google Drive API Utilities Module

This module provides a set of functions for interacting with the Google Drive API.
It allows you to authenticate with the API, upload, download, and manage files and folders in Google Drive.
"""

import logging
import pickle
import os.path
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload



def authenticate_google_drive(SCOPES : list = 'https://www.googleapis.com/auth/drive',
                              token_path : str = 'token.pickle',
                              credentials_path : str = 'credentials.json',
                              service_credentials_path : str = 'service_credentials.json') -> None:

    """
    Authenticates with the Google Drive API and returns a service object for interacting with the API.

    Parameters
    ----------
    SCOPES : str, optional
        OAuth 2.0 scope URLs for the desired access level. Default is 'https://www.googleapis.com/auth/drive'.
    token_path : str, optional
        Path to the token pickle file used to store authentication credentials. Default is 'token.pickle'.
    credentials_path : str, optional
        Path to the JSON file containing the API credentials. Default is 'credentials.json'.
    service_credentials_path : str, optional
        Path to the JSON key file for a Google Cloud service account to use for authentication.
        If provided, it will be used as an alternative to the user-based OAuth 2.0 flow.

    Returns
    -------
    googleapiclient.discovery.Resource
        A service object providing access to the Google Drive API.

    Notes
    -----
    This function authenticates the application using the OAuth 2.0 flow or a Google Cloud service account.
    If valid credentials are not available, it may run a local server to facilitate user authorization.
    The authenticated service object can be used to interact with the Google Drive API.

    Example
    -------
    >>> drive_service = authenticate_google_drive(
    ...     SCOPES='https://www.googleapis.com/auth/drive',
    ...     token_path='token.pickle',
    ...     credentials_path='credentials.json',
    ...     service_credentials_path='service_credentials.json'
    ... )
    """

    creds = None
    if os.path.exists(token_path):
        with open(token_path , 'rb') as token:
            creds = pickle.load(token)
    #if not creds or not creds.valid:
    else:

        if os.path.exists(service_credentials_path):
            creds = service_account.Credentials.from_service_account_file(service_credentials_path,
                                                                                scopes=[SCOPES])

        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                credentials_path, [SCOPES])
            creds = flow.run_local_server(port=0)
            with open(token_path , 'wb') as token:
                pickle.dump(creds, token)
    service = build('drive', 'v3', credentials=creds)
    return service

def upload_file(service,
                file_path : str,
                folder_id : str,
                overwrite : bool = True) -> str:

    """
    Uploads a file to Google Drive and returns the ID of the uploaded file.

    Parameters
    ----------
    service : googleapiclient.discovery.Resource
        An authenticated service object for interacting with the Google Drive API.
    file_path : str
        The local path of the file to be uploaded.
    folder_id : str
        The ID of the folder in Google Drive where the file should be uploaded.
    overwrite : bool, optional
        Whether to overwrite the file if it already exists in the folder. Defaults to True.

    Returns
    -------
    str
        The ID of the uploaded file on Google Drive.

    Notes
    -----
    This function uploads a file to Google Drive using the provided service object.
    The `file_path` specifies the local path of the file to be uploaded. The `folder_id`
    specifies the target folder's ID in Google Drive where the file will be uploaded.
    If `overwrite` is True and a file with the same name exists in the folder, it will be replaced.

    Example
    -------
    >>> drive_service = authenticate_google_drive()
    >>> folder_id = 'your_folder_id_here'
    >>> file_id = upload_file(drive_service, 'file_to_upload.txt', folder_id)
    """

    if overwrite:
        file_id = get_google_drive_file_id(service = service,
                                    file_name = os.path.basename(file_path),
                                    folder_id = folder_id,
                                    throw_error=False,
                                    loggerLvl='error')

        if file_id:

            delete_google_drive_item(service = service,
                                    file_id = file_id)


    file_metadata = {'name': os.path.basename(file_path), 'parents': [folder_id]}
    media = MediaFileUpload(file_path, mimetype='application/octet-stream')
    uploaded_file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id'
    ).execute()

    return uploaded_file['id']

def download_file(service,
                  file_id: str,
                  destination_path: str,
                  throw_error: bool = True,
                  logger: logging.Logger = None,
                  loggerLvl: str = 'debug') -> None:
    """
    Downloads a file from Google Drive and saves it to the specified destination path.

    Parameters
    ----------
    service : googleapiclient.discovery.Resource
        An authenticated service object for interacting with the Google Drive API.
    file_id : str
        The ID of the file in Google Drive to be downloaded.
    destination_path : str
        The local path where the downloaded file will be saved.
    throw_error : bool, optional
        Whether to raise an error if an exception occurs. Defaults to True.
    logger : logging.Logger, optional
        The logger instance to use. Defaults to None.
    loggerLvl : str, optional
        The logging level to use if a logger is created. Default is 'debug'.

    Returns
    -------
    None

    Notes
    -----
    This function downloads a file from Google Drive using the provided service object.
    The `file_id` specifies the ID of the file to be downloaded. The downloaded content
    is saved to the specified `destination_path`.

    Example
    -------
    >>> drive_service = authenticate_google_drive()
    >>> file_id = 'your_file_id_here'
    >>> download_file(drive_service, file_id, 'downloaded_file.txt')
    """

    # Create a logger if not provided
    if logger is None:
        loggerLvls = {'info' : logging.INFO,
                      'debug' : logging.DEBUG,
                      'warning' : logging.WARNING,
                      'fatal' : logging.FATAL,
                      'error' : logging.ERROR}
        logger = logging.getLogger(__name__)
        logger.setLevel(loggerLvls[loggerLvl])


    try:

        request = service.files().get_media(fileId=file_id)
        with open(destination_path, 'wb') as f:
            downloader = MediaIoBaseDownload(f, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
                logger.debug(f"Download {int(status.progress() * 100)}%")

    except Exception as e:

        logger.error("Error occured during attempt to download file!")

        if throw_error:
            raise e

        print("The error:", e)





def get_google_drive_file_id(service,
                             file_name: str,
                             folder_id: str = None,
                             throw_error: bool = True,
                             logger: logging.Logger = None,
                             loggerLvl: str = 'debug') -> str:

    """
    Gets the Google Drive file ID based on the provided parameters.

    Parameters
    ----------
    service : googleapiclient.discovery.Resource
        An authenticated service object for interacting with the Google Drive API.
    file_name : str
        The name of the file to search for.
    folder_id : str, optional
        The ID of the folder in which to search for the file. Defaults to None.
    throw_error : bool, optional
        Whether to raise an error if an exception occurs. Defaults to True.
    logger : logging.Logger, optional
        The logger instance to use. Defaults to None.
    loggerLvl : str, optional
        The logging level to use if a logger is created. Default is 'debug'.

    Returns
    -------
    str
        The file ID of the found file, or None if not found.

    Notes
    -----
    This function retrieves the file ID from Google Drive based on the provided
    file name and, optionally, folder ID. The `service` parameter should be an
    authenticated service object for the Google Drive API.

    If the `folder_id` is specified, the search is limited to that folder.
    If the file is not found or if multiple files with the same name are found,
    appropriate warnings or errors are raised based on the `throw_error` parameter.

    If `logger` is not provided, a new logger will be created using the module's name.

    Raises
    ------
    ValueError
        If no file with the specified name is found or if the name is not unique.

    Example
    -------
    >>> drive_service = authenticate_google_drive()
    >>> folder_id = 'your_folder_id_here'
    >>> file_id = get_google_drive_file_id(drive_service, 'example.txt', folder_id)
    """

    # Create a logger if not provided
    if logger is None:
        loggerLvls = {'info' : logging.INFO,
                      'debug' : logging.DEBUG,
                      'warning' : logging.WARNING,
                      'fatal' : logging.FATAL,
                      'error' : logging.ERROR}
        logger = logging.getLogger(__name__)
        logger.setLevel(loggerLvls[loggerLvl])

    try:

        # Call the Drive v3 API
        results = service.files().list(
            fields="nextPageToken, files(id, name, mimeType, size, parents, modifiedTime)").execute()
        # get the results
        items = results.get('files', [])

        # search items for the file based on name
        if folder_id:
            item = [i for i in items if 'name' in i and i['name'] == file_name and i['parents'] == [folder_id]]
        else:
            item = [i for i in items if 'name' in i and i['name'] == file_name]

        # check is there are anyt items or more then one item with the same name

        if len(item) == 0:
            logger.warning(f"File with name: {file_name} is not accessible with provided service parameter")
            if throw_error:
                raise ValueError("Resolve issues before proceesing any further!")

            file_id = None

        if len(item) > 1:
            logger.warning(f"File with name: {file_name} was not unique. Pls provide folder_id or provide different file name!")
            print(item)
            logger.warning(f"First item with name: {file_name} was chosen!")
            file_id = item[0]['id']

        if len(item) == 1:
            file_id = item[0]['id']



    except Exception as e:

        logger.error("Error occured while getting google drive file id!")

        if throw_error:
            raise e

        print("The error:", e)
        file_id = None

    return file_id



def delete_google_drive_item(service,
                             file_id: str,
                             logger: logging.Logger = None,
                             loggerLvl : str = 'debug') -> None:
    """
    Deletes an item (file or folder) from Google Drive.

    Parameters
    ----------
    service : googleapiclient.discovery.Resource
        An authenticated service object for interacting with the Google Drive API.
    file_id : str
        The ID of the item (file or folder) to be deleted.
    logger : logging.Logger, optional
        The logger instance to use. Defaults to None.
    loggerLvl : str, optional
        The logging level to use if a logger is created. Default is 'debug'.

    Returns
    -------
    None

    Notes
    -----
    This function deletes an item (file or folder) from Google Drive using the provided service object.
    The `file_id` parameter specifies the ID of the item to be deleted.

    If `logger` is not provided, a new logger will be created using the module's name.
    """

    # Create a logger if not provided
    if logger is None:
        loggerLvls = {'info' : logging.INFO,
                      'debug' : logging.DEBUG,
                      'warning' : logging.WARNING,
                      'fatal' : logging.FATAL,
                      'error' : logging.ERROR}
        logger = logging.getLogger(__name__)
        logger.setLevel(loggerLvls[loggerLvl])

    try:
        service.files().delete(fileId=file_id).execute()
        logger.debug(f"Item with ID {file_id} deleted successfully.")
    except Exception as e:
        logger.debug(f"An error occurred while deleting item with ID {file_id}: {e}")
