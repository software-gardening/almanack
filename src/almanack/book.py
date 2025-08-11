"""
Module for interacting with Software Gardening
Almanack book content through a Python package.
"""

import pathlib
from typing import Optional

import yaml


# Example of displaying a specific chapter
def read(chapter_name: Optional[str] = None):
    """
    A function for reading almanack content through a package
    interface.

    Args:
        chapter_name: Optional[str], default None
            A string which indicates the short-hand name of a chapter
            from the book. Short-hand names are lower-case title names
            read from `src/book/_toc.yml`.

    Returns:
        None
            The outcome of this function involves printing the
            content of the selected chapter from the short-hand
            name or showing available chapter names through an exception.
    """

    # gather base path for book content
    book_base_path = pathlib.Path(__file__).parent.parent / "book"

    # read the table of contents
    with open(book_base_path / "_toc.yml", "r") as file:
        toc = yaml.safe_load(file)

    # prepare a chapter paths dictionary
    chapter_paths = {}

    # Iterate through the main chapters
    for chapter in toc["parts"][0]["chapters"]:
        title_key = chapter["title"].replace(" ", "_").lower()
        chapter_paths[title_key] = chapter["file"]

        # Check if there are sections within the chapter
        if "sections" in chapter:
            for section in chapter["sections"]:
                # we pass the glob sections as it is not a direct file.
                if "glob" in section:
                    pass
                elif "title" in section and "file" in section:
                    section_title_key = section["title"].replace(" ", "_").lower()
                    chapter_paths[section_title_key] = section["file"]

    # if we don't find the chapter, raise a helpful exception message
    if chapter_name not in chapter_paths:
        raise LookupError(
            (
                f"Unable to find content under name {chapter_name}.\n"
                "Please use one of the following names to access content:\n",
                "\n".join(chapter_paths.keys()),
            )
        )

    # else we read the content
    with open(str(book_base_path / chapter_paths[chapter_name])) as file:
        print(file.read())  # noqa: T201
