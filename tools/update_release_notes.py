import os
import sys
from package_auto_assembler import ReleaseNotesHandler



if __name__ == "__main__":

    label_name = sys.argv[1]
    version = sys.argv[2]

    release_notes_path = "./release_notes"
    release_notes_filepath = os.path.join(release_notes_path,
                                          f"{label_name}.md")


    rnh = ReleaseNotesHandler(
        filepath = release_notes_filepath,
        label_name = label_name,
        version = version,
        max_search_depth = 2
    )

    rnh.save_release_notes()

