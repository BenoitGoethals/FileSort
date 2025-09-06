import asyncio

import argparse
import os
from pathlib import Path
import shutil

CPU_WORKERS = os.cpu_count()

class FileManager:
    def __init__(self, source: str, destination: str, file_types: list[str]) -> None:
        self.source = Path(source)
        self.destination = Path(destination)
        self.file_types = file_types

    async def move_files(self) -> bool:
        if not self.destination.exists():
            self.destination.mkdir(parents=True, exist_ok=True)
        dl_semaphore = asyncio.Semaphore()
        source_files = []
        if self.file_types is not None:
            wanted = {t.lower().lstrip(".") for t in self.file_types}
        else:
            wanted = None

        for path in self.source.rglob("*"):
            if path.is_file():
                if wanted is None:
                    source_files.append(path)
                else:
                    ext = path.suffix.lower().lstrip(".")
                    if ext in wanted:
                        source_files.append(path)

        async with asyncio.TaskGroup() as tg:
            tasks = [
                tg.create_task(
                    self.move_file_suffix_dest(file, dl_semaphore)
                )
                for file_nr, file in enumerate(source_files, start=1)
            ]

        return any([task.result() for task in tasks])

    async def move_file_suffix_dest(self, source_file: Path, semaphore: asyncio.Semaphore,) -> bool:
        try:
            async with semaphore:
                if len(source_file.suffixes) == 1 and source_file.suffix:
                    suffix = source_file.suffix.lstrip(".")
                else:
                    suffix = "other"
                dest_path = self.destination / suffix
                if not dest_path.exists():
                    dest_path.mkdir(parents=True, exist_ok=True)
                destination_file = dest_path / source_file.name
                shutil.move(str(source_file), str(destination_file))
                print(f"Moved {source_file} to {destination_file}")
                return True
        except asyncio.CancelledError:
            print(f"Cancelled moving {source_file}")
            return False

    def remove_folder_source(self):
        try:
            shutil.rmtree(self.source)
            print(f"Removed source folder {self.source}")
        except FileNotFoundError:
            print(f"Source folder {self.source} does not exist")
        except PermissionError:
            print(f"Permission denied when trying to remove {self.source}")
        except OSError as e:
            print(f"Error removing source folder {self.source}: {str(e)}")


async def start(source_path: str, dest_path: str, file_type: list[str]) -> None:
    file_manager = FileManager(source_path, dest_path, file_type)
    status=await file_manager.move_files()
    if not status:
        print("No files moved.")
    elif status:
        print("All files moved.")
    else:
        print("Some files could not be moved.")
    if file_type is None:
        file_manager.remove_folder_source()




def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Move files of a specific type from source to destination.")
    parser.add_argument("-s", "-source", "--source", dest="source", required=True, help="Source directory")
    parser.add_argument("-d", "-destination", "--destination", dest="destination", required=True,
                        help="Destination directory")
    parser.add_argument("-t", "-type", "--type", dest="file_type",  nargs="+",
                        help="File type/extension to move (e.g., txt pdf jpeg)")
    return parser.parse_args()


async def main() -> None:
    args = parse_args()
    await start(args.source, args.destination, args.file_type)


if __name__ == "__main__":
    asyncio.run(main())
