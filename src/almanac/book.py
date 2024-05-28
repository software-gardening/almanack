import pathlib

# Example of displaying a specific chapter
def display_chapter(chapter_name):
    chapter_path = pathlib.Path(__file__).parent.parent / 'book' / chapter_name
    
    if not chapter_path.exists():
        print(f"Chapter {chapter_name} not found.")
        return
    
    with chapter_path.open() as file:
        print(file.read())
