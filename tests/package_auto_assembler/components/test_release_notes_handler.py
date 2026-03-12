from python_modules.components.paa_deps.release_notes_handler import ReleaseNotesHandler


def test_release_notes_handler_processes_commits_and_saves_notes(tmp_path):
    notes_file = tmp_path / "release_notes.md"
    handler = ReleaseNotesHandler(
        filepath=str(notes_file),
        label_name="mypkg",
        commit_messages=["[mypkg][.+.] add parser; fix docs", "[other] ignore"],
    )

    assert notes_file.exists()
    assert handler.filtered_messages == ["[mypkg][.+.] add parser; fix docs"]
    assert "add parser" in handler.processed_messages
    assert "fix docs" in handler.processed_messages
    assert handler.extract_version_update() == "minor"

    handler.create_release_note_entry(version="1.3.0", new_messages=handler.processed_messages)
    handler.save_release_notes()

    content = notes_file.read_text(encoding="utf-8")
    assert "### 1.3.0" in content
    assert "- add parser" in content


def test_release_notes_handler_matches_hyphenated_commit_tags(tmp_path):
    notes_file = tmp_path / "release_notes.md"
    handler = ReleaseNotesHandler(
        filepath=str(notes_file),
        label_name="my_pkg",
        commit_messages=["[my-pkg][.+.] add parser; fix docs", "[other] ignore"],
    )

    assert handler.filtered_messages == ["[my-pkg][.+.] add parser; fix docs"]
    assert "add parser" in handler.processed_messages
    assert handler.extract_version_update() == "minor"
