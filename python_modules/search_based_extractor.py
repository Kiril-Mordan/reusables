# Imports
## essential
import logging
import attr
## requests
import requests
## scraper lib
from bs4 import BeautifulSoup, Tag, Comment


def extract_visible_text(soup):
    """
    Extracts visible text from a BeautifulSoup object.
    """
    texts = []

    for element in soup.recursiveChildGenerator():
        if isinstance(element, Comment):  # Skip comments
            continue
        if isinstance(element, Tag):
            if element.name in ["script", "style"]:  # Skip script/style tags
                continue
        if isinstance(element, str):  # NavigableString
            stripped = element.strip()
            if stripped:
                texts.append(stripped)

    return ' '.join(texts)

def find_element_by_text(soup, search_text : str):
    """
    Finds the first element containing the search_text and returns the path to it.
    """
    path = []
    found_element = None

    def helper(element, search_text):
        nonlocal found_element
        if isinstance(element, Tag):
            siblings = [sib for sib in element.previous_siblings if isinstance(sib, Tag) and sib.name == element.name]

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

    found = helper(soup, search_text)
    return found_element, path if found else (None, [])

def extract_from_path(soup,
                     path : list,
                     search_text : str,
                     context_len : int = 30,
                     start_from_search : bool = True,
                     end_after_search : bool = False) -> str:
    """
    Traverses the BeautifulSoup tree based on the provided path and returns the search term
    and some context from the target element.
    """
    element = soup
    for tag, position in path:
        if tag == '[document]':  # This is the entire document, so just continue
            continue
        # Find all children that match the tag
        matching_children = [child for child in element.children if isinstance(child, Tag) and child.name == tag]
        if position < len(matching_children):
            element = matching_children[position]
        else:
            raise ValueError(f"Cannot navigate to {tag} at position {position}")

    full_text = element.get_text()
    search_start = full_text.find(search_text)

    # Extract context around the found text
    if start_from_search:
        start = max(0, search_start - context_len)
    else:
        start = 0

    if end_after_search:
        end = min(len(full_text), search_start + len(search_text) + context_len)
    else:
        end = len(full_text)

    return full_text[start:end]


