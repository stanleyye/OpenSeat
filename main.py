import aiohttp
import argparse
import asyncio
import async_timeout
from pathlib import Path
from twilio.rest import Client

courses_file_name = 'courses.txt'
courses_to_search = []
start_url = 'https://courses.students.ubc.ca/cs/main?pname=subjarea&tname=subjareas&req=0'

client = None
email_recipient = None
email_sender = None
has_email_option = False
has_sms_option = False
secret_id = None
sms_recipient = None
sms_sender = None
twilio_auth_token = None


def read_file(file):
    with file.open() as f:
        for line in f:
            # if line is empty, continue
            if not line:
                continue

            # normalize the string to upper case + trimmed
            course = line.replace('\n', '').strip().upper()
            print(course)
            courses_to_search.append(course)

def parser():
    parser = argparse.ArgumentParser(
        description='Get notified when a UBC course seat is available'
    )
    parser.add_argument('-er', '-email_recipient', type=str, help='The email address to send a notification to.')
    parser.add_argument('-es', '-email_sender', type=str, help='The email address of the sender.')
    parser.add_argument('-sid', '-secret_id', type=str, help='Your Twilio account\'s secret ID.')
    parser.add_argument('-sr', '-sms_recipient', type=str, help='The receiver of the SMS message.')
    parser.add_argument('-ss', '-sms_sender', type=str, help='Your Twilio-managed phone number.')
    parser.add_argument('-t', '-token', type=str, help='The Twilio authentication token.')
    return parser

def validate_cmd_args(cmd_args):
    if not cmd_args:
        raise ValueError('No command arguments specified.')

    email_args_count = 0

    if 'er' in cmd_args and cmd_args.er:
        email_args_count += 1

    if 'es' in cmd_args and cmd_args.es:
        email_args_count += 1

    if email_args_count == 2:
        global has_email_option, email_recipient, email_sender
        has_email_option = True
        email_recipient = cmd_args.er
        email_sender = cmd_args.es
    elif email_args_count == 1:
        raise ValueError('Either Email sender or recipient are missing')

    sms_args_count = 0

    if 'sid' in cmd_args and cmd_args.sid:
        print(cmd_args.sid)
        sms_args_count += 1

    if 'sr' in cmd_args and cmd_args.sr:
        sms_args_count += 1

    if 'ss' in cmd_args and cmd_args.ss:
        sms_args_count += 1

    if 't' in cmd_args and cmd_args.t:
        sms_args_count += 1

    if sms_args_count == 4:
        global has_sms_option, secret_id, sms_recipient, sms_sender, twilio_auth_token
        has_sms_option = True
        secret_id = cmd_args.sid
        sms_recipient = cmd_args.sr
        sms_sender = cmd_args.ss
        twilio_auth_token = cmd_args.t
    elif sms_args_count > 0 and sms_args_count < 4:
        raise ValueError('Missing either the Twilio auth token, Twio Secret ID, SMS Sender or the SMS Recipient')


async def fetch(session, url, course, course_name_split, course_name_split_length, count):
    # timeout if no response in 10 seconds
    with async_timeout.timeout(10):
        async with session.get(url) as response:
            return await response.text()

async def main():
    courses = Path('./courses.txt')

    # Check whether courses.txt is defined
    if not courses.is_file():
        print('courses.txt does not exist.')
        return

    # read the file and put the courses into a list
    read_file(courses)
    print(*courses_to_search, sep='\n')

    # create a client session and then asynchronously check the course pages
    async with aiohttp.ClientSession() as session:
        futures = []
        for course in courses_to_search:
            future = fetch(session, start_url, course, course.split(' '), len(course.split(' ')), 0)
            print(future)
            futures.append(future)
        
        await asyncio.gather(*futures)


if __name__ == '__main__':
    parser = parser()
    cmd_args = parser.parse_args()
    print(cmd_args)
    validate_cmd_args(cmd_args)

    print(has_sms_option)
    if has_sms_option:
        client = Client(secret_id, twilio_auth_token)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
