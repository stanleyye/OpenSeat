import aiohttp
import argparse
import asyncio
import async_timeout
from pathlib import Path

courses_to_search = []
start_url = "https://courses.students.ubc.ca/cs/main?pname=subjarea&tname=subjareas&req=0"

async def fetch(session, url, course, course_name_split, course_name_split_length, count):
    # timeout if no response in 10 seconds
    with async_timeout.timeout(10):
        async with session.get(url) as response:
            # TODO


def read_file(file):
    with open(file) as f:
        for line in f:
            # if line is empty, continue
            if not line:
                continue

            # normalize the string to upper case + trimmed
            course = line.replace("\n", "").strip().upper()
            courses_to_search.append(course)

async def main(loop):
    print("Starting main function", "\n")

    courses = Path("courses.txt")

    # Check whether courses.txt is defined
    if not courses.is_file():
        print("courses.txt does not exist.")
        return

    # read the file and put the courses into a list
    read_file(courses)
    print(*courses_to_search, sep='\n')

    # create a client session and then asynchronously check the course pages
    async with aiohttp.ClientSession(loop=loop) as session:
        tasks = [
            fetch(session, start_url, course, course.split(" "), len(course.split(" ")), 0)
            for course in courses_to_search
        ]
        await asyncio.gather(*tasks)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(loop))
