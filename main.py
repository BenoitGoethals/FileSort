import asyncio

import argparse
import os
import shutil

CPU_WORKERS = os.cpu_count()

class FileManager:
    def __init__(self, source: str, destination: str, file_types: list[str]) -> None:
        self.source = source
        self.destination = destination
        self.file_types = file_types

    async def move_files(self) -> bool:
        if not os.path.exists(self.destination):
            os.makedirs(self.destination)
        dl_semaphore = asyncio.Semaphore()
        source_files = []
        for root, _, files in os.walk(self.source):
            for file in files:
                if self.file_types is not None:
                     for type_file in self.file_types:
                        if file.endswith(type_file):
                            source_file = os.path.join(root, file)
                            source_files.append(source_file)
                else:
                    source_file = os.path.join(root, file)
                    source_files.append(source_file)
        async with asyncio.TaskGroup() as tg:
            tasks = [
                tg.create_task(
                    self.move_file_suffix_dest(file, dl_semaphore)
                )
                for file_nr,file in enumerate(source_files, start=1)
            ]

        return any([task.result() for task in tasks])


    async def move_file_suffix_dest(self,source_file: str, semaphore: asyncio.Semaphore,) -> bool:
        try:
            async with semaphore:
                suffix =source_file.split(".")[-1]
                dest_path = os.path.join(self.destination,suffix)
                if not os.path.exists(dest_path):
                    os.makedirs(dest_path)
                destination_file = os.path.join(self.destination,suffix, os.path.basename(source_file),)
                shutil.move(source_file, destination_file)
                print(f"Moved {source_file} to {destination_file}")
                return True
        except asyncio.CancelledError:
            print(f"Cancelled moving {source_file}")
            return False




async def start(source_path: str, dest_path: str, file_type: list[str]) -> None:
    file_manager = FileManager(source_path, dest_path, file_type)
    status=await file_manager.move_files()
    if not status:
        print("No files moved.")
    elif status:
        print("All files moved.")
    else:
        print("Some files could not be moved.")





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
