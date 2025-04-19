import os

def extract_directory(path : str):

    """
    Simple function to extract directory name from path and create one if it does not exist
    """

    if os.path.isdir(path):
        # If the path is a directory, return it as is
        return path
    if os.path.isfile(path):
        # If the path is a file, return its directory
        return os.path.dirname(path)

    # If the path does not exist, make dir
    os.makedirs(path)
    return path
