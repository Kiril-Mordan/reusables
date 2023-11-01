"""
Search Based Extractor

Utility to simplify webscraping by taking advantave of search and assumptions about html structure.
Extractor allows to find parent html element that contains searched term, record path to it in a file
and reuse that to scrape data with same html structure.
"""


# Imports
## essential
import json
import logging
import attr
## requests
import requests
## scraper lib
from bs4 import BeautifulSoup, Tag, Comment


@attr.s
class SearchBasedExtractor:
    # pylint: disable=too-many-instance-attributes

    """
    A utility class designed to extract specific content from web pages based on search terms.

    Attributes:
        soup (BeautifulSoup): A BeautifulSoup object representing the parsed HTML.
        filename (str): Name of the file to save or load paths.
        logger (logging.Logger): A logger instance for logging messages.
        logger_name (str): Name assigned to the logger.
        loggerLvl (int): Logging level.
        link (str): The web link from which the soup is generated.
        found_element (Tag): The element containing the searched text.
        path (list): List of tuples representing the path to the found_element.
        searched_text (str): Text that was searched.
    """

    soup = attr.ib(default=None)
    filename = attr.ib(default='recorded_sbe.json')

    logger = attr.ib(default=None)
    logger_name = attr.ib(default='SearchBasedExtractor')
    loggerLvl = attr.ib(default=logging.INFO)

    link = attr.ib(default=None, init=False)
    found_element = attr.ib(default=None, init=False)
    path = attr.ib(default=[], init=False)
    extracted_visible_text = attr.ib(default=None, init=False)
    searched_text = attr.ib(default='', init=False)


    def __attrs_post_init__(self):
        self.initialize_logger()

    def initialize_logger(self):

        """
        Initialize a logger for the class instance based on
        the specified logging level and logger name.
        """

        if self.logger is None:
            logging.basicConfig(level=self.loggerLvl)
            logger = logging.getLogger(self.logger_name)
            logger.setLevel(self.loggerLvl)

            self.logger = logger

    def initialize_soup(self, link : str, reset : bool = True):

        """
        Initialize a soup for the class instance based on the specified link.
        """

        if (self.soup is None) or reset:

            if link:
                try:
                    response = requests.get(link, timeout=(5,15))
                    response.raise_for_status()
                except Exception as e:
                    self.logger.error("Provided link was unreachable!")
                    print(e)

            else:
                self.logger.error("Link is missing!")
                self.logger.error("Either provide 'soup' parameter or 'link' parameter!")
                raise ValueError("Missing 'link' parameter!")

            self.soup = BeautifulSoup(response.content, 'html.parser')
            self.link = link


    def extract_visible_text(self, new_line_separator : str = '\n'):
        """
        Extracts visible text from a BeautifulSoup object.
        """

        if self.extracted_visible_text:
            self.logger.warning("Visibile text was already extracted, returning extracted text!")
        else:
            texts = []

            for element in self.soup.recursiveChildGenerator():
                if isinstance(element, Comment):  # Skip comments
                    continue
                if isinstance(element, Tag):
                    if element.name in ["script", "style"]:  # Skip script/style tags
                        continue
                if isinstance(element, str):  # NavigableString
                    stripped = element.strip()
                    if stripped:
                        texts.append(stripped + new_line_separator)

            self.extracted_visible_text = ' '.join(texts)

        return self.extracted_visible_text

    def find_path_with_text(self, search_text : str):
        """
        Finds the first element containing the search_text and returns the path to it.
        """
        path = []
        found_element = None

        def helper(element, search_text):
            nonlocal found_element
            if isinstance(element, Tag):
                siblings = [sib for sib in element.previous_siblings \
                    if isinstance(sib, Tag) and sib.name == element.name]

                position = len(siblings)
                path.append((element.name, position))

                for child in element.children:
                    found = helper(child, search_text)
                    if found:
                        return True

                path.pop()  # Remove the current tag from the path if text not found in this subtree

            if isinstance(element, str):  # NavigableString
                stripped = element.strip()
                if search_text in stripped:
                    found_element = element.parent  # save the parent tag
                    return True

            return False

        found = helper(self.soup, search_text)

        if found:
            self.searched_text = search_text
            self.found_element = found_element
            self.path = path
        else:
            self.logger.warning("Provided search term was not found in the connected soup!")

    def save_recorded_sbe(self, filename : str = None):

        """
        Saves the path, link, and searched_text to a JSON file.
        """

        if filename is None:
            filename = self.filename

        data = {
            "path": self.path,
            "link": self.link,
            "searched_text": self.searched_text
        }
        with open(self.filename, 'w') as f:
            json.dump(data, f)
        self.logger.info(f"Data saved to '{self.filename}'")

    def load_recorded_sbe(self, filename : str = None):

        """
        Loads only the path from a JSON file.
        """

        if filename is None:
            filename = self.filename

        with open(self.filename, 'r') as f:
            data = json.load(f)
        self.path = data["path"]
        self.logger.info(f"Path loaded from {self.filename}")

    def show_recorded_sbe(self, filename : str = None):

        """
        Displays the link, searched_text, and path from a JSON file.
        """

        if filename is None:
            filename = self.filename

        with open(filename, 'r') as f:
            data = json.load(f)

        print("Link:", data.get("link", "N/A"))
        print("Searched Text:", data.get("searched_text", "N/A"))
        print("Path:", data.get("path", []))



    def extract_from_path(self,
                        search_text_start : str = '',
                        search_text_end : str = '',
                        context_len : int = 0) -> str:
        """
        Traverses the BeautifulSoup tree based on the provided path and returns the search term
        and some context from the target element.
        """

        if self.soup is None:
            raise ValueError("Missing 'soup' parameter!")

        if self.path == []:
            raise ValueError("Missing 'path' parameter!")


        element = self.soup
        for tag, position in self.path:
            if tag == '[document]':  # This is the entire document, so just continue
                continue
            # Find all children that match the tag
            matching_children = [child for child in element.children \
                if isinstance(child, Tag) and child.name == tag]
            if position < len(matching_children):
                element = matching_children[position]
            else:
                raise ValueError(f"Cannot navigate to {tag} at position {position}")

        full_text = element.get_text()

        # Extract context around the found text
        if search_text_start != '':
            search_start = full_text.find(search_text_start)
            start = max(0, search_start - context_len)
        else:
            start = 0


        if search_text_end != '':
            search_end = full_text.find(search_text_end)

            end = max(start, search_end + context_len)

        else:

            end = len(full_text)

        return full_text[start:end]
