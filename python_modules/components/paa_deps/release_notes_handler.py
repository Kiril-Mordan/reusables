import logging
import os
import re
import subprocess
import attr #>=22.2.0

@attr.s
class ReleaseNotesHandler:

    """
    Contains set of tools to handle release notes from commit messages.
    """

    # inputs
    filepath = attr.ib(default='release_notes.md', type=str)
    label_name = attr.ib(default=None, type=list)
    version = attr.ib(default='0.0.1', type=str)
    max_search_depth = attr.ib(default=2, type=int)

    # processed
    n_last_messages = attr.ib(default=1, type=int)
    existing_contents = attr.ib(default=None, type=list)
    commit_messages = attr.ib(default=None, type=list)
    filtered_messages = attr.ib(default=None, type=list)
    processed_messages = attr.ib(default=None, type=list)
    processed_note_entries  = attr.ib(default=None, type=list)
    version_update_label = attr.ib(default=None, type=str)


    logger = attr.ib(default=None)
    logger_name = attr.ib(default='Release Notes Handler')
    loggerLvl = attr.ib(default=logging.INFO)
    logger_format = attr.ib(default=None)

    def __attrs_post_init__(self):
        self._initialize_logger()

        if self.filepath:

            self._initialize_notes()

            if self.existing_contents is None:
                self.existing_contents = self.get_release_notes_content()

        if self.commit_messages is None:
            self._get_commits_since_last_merge()
        if self.filtered_messages is not []:
            self._filter_commit_messages_by_package()
        if self.processed_messages is None:
            self._clean_and_split_commit_messages()
        # if self.processed_note_entries is None:
        #     self._create_release_note_entry()


    def _initialize_logger(self):

        """
        Initialize a logger for the class instance based on the specified logging level and logger name.
        """

        if self.logger is None:
            logging.basicConfig(level=self.loggerLvl, format=self.logger_format)
            logger = logging.getLogger(self.logger_name)
            logger.setLevel(self.loggerLvl)

            self.logger = logger

    def _initialize_notes(self):

        if not os.path.exists(self.filepath):
            self.logger.warning(f"No release notes were found in {self.filepath}, new will be initialized!")

            content = """# Release notes\n"""
            with open(self.filepath, 'w', encoding='utf-8') as file:
                file.write(content)

    def _deduplicate_with_exceptions(self,
                                     lst : list):

        seen = set()
        deduplicated = []
        version_headers = set()

        # Reverse iteration
        for item in reversed(lst):
            # If it's a version header, handle it differently
            if item.startswith("###"):
                if item not in version_headers:
                    version_headers.add(item)
                    if deduplicated and deduplicated[-1] != "\n":
                        deduplicated.append("\n")
                    deduplicated.append(item)
                    deduplicated.append("\n")  # Ensure newline after version header
            else:
                if item not in seen:
                    if item == "\n" and (not deduplicated or deduplicated[-1] == "\n"):
                        # Skip consecutive newlines
                        continue
                    seen.add(item)
                    deduplicated.append(item)
                    if item != "\n" and (deduplicated and deduplicated[-1] != "\n"):
                        deduplicated.append("\n")  # Ensure newline after each item

        # Reverse the result to restore original order
        deduplicated.reverse()

        # Clean up leading and trailing newlines
        while deduplicated and deduplicated[0] == "\n":
            deduplicated.pop(0)
        while deduplicated and deduplicated[-1] == "\n":
            deduplicated.pop()

        return deduplicated

    def _get_commits_since_last_merge(self, n_last_messages : int = 1):

        # First, find the last merge commit
        find_merge_command = ["git", "log", "--merges", "--format=%H", "-n", str(n_last_messages)]
        merge_result = subprocess.run(find_merge_command, capture_output=True, text=True)
        if merge_result.returncode != 0:
            #raise Exception("Failed to find last merge commit")
            self.logger.warning("Failed to find last merge commit")
            self.commit_messages = []
            return True

        merge_result_p = merge_result.stdout.strip().split("\n")

        if len(merge_result_p) > (n_last_messages-1):
            last_merge_commit_hash = merge_result_p[n_last_messages-1]
        else:
            last_merge_commit_hash = None
        if not last_merge_commit_hash:
            self.logger.warning("No merge commits found")
            self.commit_messages = []
            return True

        # Now, get all commits after the last merge commit
        log_command = ["git", "log", f"{last_merge_commit_hash}..HEAD", "--no-merges", "--format=%s"]
        log_result = subprocess.run(log_command, capture_output=True, text=True)
        if log_result.returncode != 0:
            #raise Exception("Error running git log")
            self.logger.warning("Error running git log")
            self.commit_messages = []
            return True

        # Each commit message is separated by newlines
        commit_messages = log_result.stdout.strip().split("\n")

        self.commit_messages = commit_messages

    def _filter_commit_messages_by_package(self,
                                           commit_messages : list = None,
                                           label_name : str = None):

        if commit_messages is None:
            commit_messages = self.commit_messages

        if label_name is None:
            label_name = self.label_name

        # This pattern will match messages that start with optional spaces, followed by [<package_name>],
        # possibly surrounded by spaces, and then any text. It is case-sensitive.
        pattern = re.compile(rf'\s*\[\s*{re.escape(label_name)}\s*\].*')

        # Filter messages that match the pattern
        filtered_messages = [msg for msg in commit_messages if pattern.search(msg)]

        if filtered_messages == []:
            self.n_last_messages += 1
            self.logger.warning(f"No relevant commit messages found!")
            if self.n_last_messages <= self.max_search_depth:
                self.logger.warning(f"..trying depth {self.n_last_messages} !")
                self._get_commits_since_last_merge(n_last_messages = self.n_last_messages)
                self._filter_commit_messages_by_package(
                    label_name = label_name)
                filtered_messages = self.filtered_messages

        self.filtered_messages = filtered_messages


    def _clean_and_split_commit_messages(self,
                                         commit_messages : list = None):

        if commit_messages is None:
            commit_messages = self.filtered_messages

        # Remove the package name tag and split messages by ";"
        cleaned_and_split_messages = []
        tag_pattern = re.compile(r'\[\s*[^]]*\]\s*')  # Matches the package name tag

        if len(commit_messages) == 0:
            self.logger.warning("No messages to clean were provided")
            cleaned_and_split_messages = []
        else:
            for msg in commit_messages:
                # Remove the package name tag from the message
                clean_msg = tag_pattern.sub('', msg).strip()
                # Split the message by ";"
                split_messages = clean_msg.split(';')
                # Strip whitespace from each split message and filter out any empty strings
                split_messages = [message.strip() for message in split_messages if message.strip()]
                cleaned_and_split_messages.extend(split_messages)

        self.processed_messages = cleaned_and_split_messages

    # Function to convert version string to a tuple of integers
    def _version_key(self, version : str):
        return tuple(map(int, version.split('.')))

    def extract_version_update(self, commit_messages : list = None):

        """
        Extract the second set of brackets and recognize version update.
        """

        if commit_messages is None:
            commit_messages = self.filtered_messages

        versions = []
        major = None
        minor = None
        patch = None

        for commit_message in commit_messages:
            match = re.search(r'\[([^\]]+)]\[([^\]]+)]', commit_message)
            if match:
                second_bracket_content = match.group(2)
                if re.match(r'^\d+\.\d+\.\d+$', second_bracket_content):
                    version = second_bracket_content
                    versions.append(version)
                elif second_bracket_content in ['+','+.','+..']:
                    major = 'major'
                elif second_bracket_content in ['.+','.+.']:
                    minor = 'minor'
                elif second_bracket_content in ['..+']:
                    patch = 'patch'

        # Return the highest priority match
        if versions:
            # Sort the list using the custom key function
            version = sorted(versions, key=self._version_key)[-1]

            self.version = version
            return version
        elif major:
            self.version_update_label = major
            return major
        elif minor:
            self.version_update_label = minor
            return minor
        elif patch:
            self.version_update_label = patch
            return patch
        else:
            self.version_update_label = 'patch'
            return patch

    def extract_latest_version(self, release_notes : list = None):

        """
        Extracts latest version from provided release notes.
        """

        if release_notes is None:
            release_notes = self.existing_contents

        latest_version = None

        for line in release_notes:
            line = line.strip()
            if line.startswith("###"):
                # Extract the version number after ###
                version = line.split("###")[-1].strip()
                # Update the latest version to the first version found
                if latest_version is None or version > latest_version:
                    latest_version = version

        return latest_version

    def create_release_note_entry(self,
                                  existing_contents : str = None,
                                  version : str = None,
                                  new_messages : list = None):

        if self.processed_note_entries is not None:
            self.logger.warning("Processed note entries already exist and will be overwritten!")

        if existing_contents is None:
            if self.existing_contents is not None:
                existing_contents = self.existing_contents.copy()


        if version is None:
            version = self.version

        if new_messages is None:
            new_messages = self.processed_messages

        # Prepare the new release note section
        # new_release_note = f"### {version}\n\n"
        # for msg in new_messages:
        #     new_release_note += f"    - {msg}\n"

        if new_messages:
            new_release_notes = [f"### {version}\n"] + ["\n"]
            for msg in new_messages:
                new_release_notes += [f"    - {msg}\n"]
        else:
            new_release_notes = []

        # If there are existing contents, integrate the new entry
        if existing_contents:
            # Find the location of the first version heading to insert the new release note right after
            index = 0
            for line in existing_contents:
                if line.strip().startswith('###'):
                    break
                index += 1

            # Insert the new release note section into the contents
            for new_release_note in new_release_notes:
                existing_contents.insert(index, new_release_note)
                index += 1
        else:

            # If no existing contents, start a new list of contents
            existing_contents = ["# Release notes\n"] + ["\n"]
            for new_release_note in new_release_notes:
                existing_contents += new_release_note

        existing_contents = self._deduplicate_with_exceptions(
            lst=existing_contents)

        self.processed_note_entries = existing_contents

    def get_release_notes_content(self,
                                  filepath : str = None) -> str:

        """
        Get release notes content.
        """

        if filepath is None:
            filepath = self.filepath

        if os.path.exists(filepath):
            # Read the existing release notes
            with open(filepath, 'r') as file:
                content = file.readlines()
        else:
            # No existing file, start with empty contents
            content = None

        return content

    def save_release_notes(self,
                           filepath : str = None,
                           note_entries : str = None):

        """
        Save updated release notes content.
        """

        if filepath is None:
            filepath = self.filepath

        if note_entries is None:
            note_entries = self.processed_note_entries

        if self.processed_messages != []:
            # Write the updated or new contents back to the file
            with open(filepath, 'w') as file:
                file.writelines(note_entries)