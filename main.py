import aiohttp
import argparse
import asyncio
import async_timeout
import re
import smtplib

from bs4 import BeautifulSoup
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from twilio.rest import Client
from urllib.parse import urlparse

courses_file_name = 'courses.txt'
courses_to_search = []
total_seats_remaining_text = 'Total Seats Remaining:'

start_url = 'https://courses.students.ubc.ca/cs/main?pname=subjarea&tname=subjareas&req=0'
parsed_url = urlparse(start_url)
# Domain is used because all the anchor tag links are relative
domain = '{uri.scheme}://{uri.netloc}'.format(uri=parsed_url)

parser_type = 'html.parser'
# Regex for line breaks and whitespace
spaces_regex = '\n*\s*\n*'

# SMS
has_sms_option = False
client = None
secret_id = None
sms_recipient = None
sms_sender = None
twilio_auth_token = None

# Email
has_email_option = False
email_server = None
email_password = None
email_recipient = None
email_sender = None

def read_file(file):
    with file.open() as f:
        for line in f:
            # if line is empty, continue
            if not line:
                continue

            # normalize the string to upper case + trimmed
            course = line.replace('\n', '').strip().upper()
            courses_to_search.append(course)

def parser():
    parser = argparse.ArgumentParser(description='Get notified when a UBC course seat is available')
    parser.add_argument('-ep', '--email_password', type=str, help='Your email password')
    parser.add_argument('-er', '--email_recipient', type=str, help='The email address to send a notification to')
    parser.add_argument('-es', '--email_sender', type=str, help='The email address of the sender')
    parser.add_argument('-sid', '--secret_id', type=str, help='Your Twilio account\'s secret ID')
    parser.add_argument('-sr', '--sms_recipient', type=str, help='The phone number to receive the SMS message')
    parser.add_argument('-ss', '--sms_sender', type=str, help='Your Twilio-managed phone number')
    parser.add_argument('-t', '--token', type=str, help='Your Twilio authentication token')
    return parser

def validate_cmd_args(cmd_args):
    email_args_count = 0

    if 'ep' in cmd_args and cmd_args.ep:
        email_args_count += 1

    if 'er' in cmd_args and cmd_args.er:
        email_args_count += 1

    if 'es' in cmd_args and cmd_args.es:
        email_args_count += 1

    if email_args_count == 3:
        global has_email_option, email_password, email_recipient, email_sender
        has_email_option = True
        email_password = cmd_args.ep
        email_recipient = cmd_args.er
        email_sender = cmd_args.es
    elif email_args_count > 0 and email_args_count < 3:
        raise ValueError('One or more of the following arguments are missing: email password, sender or recipient')

    sms_args_count = 0

    if 'sid' in cmd_args and cmd_args.sid:
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

    if email_args_count == 0 and sms_args_count == 0:
        raise ValueError('No command arguments specified.')

async def fetch(session, url, course, text_to_find, course_name_split, count):
    # timeout if no response in 10 seconds
    with async_timeout.timeout(10):
        async with session.get(url) as response:
            html_response = await response.text()

            soup = BeautifulSoup(html_response, parser_type)

            if count > 2:
                td_element = soup.find('td', text=total_seats_remaining_text)

                if td_element is not None:
                    num_of_open_spots = int(td_element.find_next_sibling('td').strong.text)

                    if num_of_open_spots > 0:
                        if has_sms_option:
                            await send_sms(course)
                        elif has_email_option:
                            await send_email(course)

                    print('There are {} open seats in {}'.format(num_of_open_spots, course))
                else:
                    print('Cannot find number of seats for', course)
            else:
                next_text_to_find = None

                href_element = soup.find('a', text=re.compile(spaces_regex + text_to_find + spaces_regex))
                href_element_link = href_element['href']
                next_url = domain + href_element_link

                if count < 2:
                    next_text_to_find = text_to_find + ' ' + course_name_split[count + 1]

                await fetch(
                    session,
                    next_url,
                    course,
                    next_text_to_find,
                    course_name_split,
                    count + 1
                )

async def send_email(course):
    msg = MIMEMultipart()
    msg['From'] = email_sender
    msg['To'] = email_recipient
    msg['Subject'] = 'OpenSeat - {}'.format(course)

    body = 'There is an open seat in {}.'.format(course)
    msg.attach(MIMEText(body,'plain'))

    msg_text = msg.as_string()
    email_server.sendmail(email_sender, email_recipient, msg_text)

async def send_sms(course):
    client.messages.create(
        to=sms_recipient,
        from_=sms_sender,
        body='A spot is available in {}.'.format(course)
    )

async def main():
    courses = Path('./courses.txt')

    # Check whether courses.txt is defined
    if not courses.is_file():
        print('courses.txt does not exist.')
        return

    # Read the file and put the courses into a list
    read_file(courses)

    # Create a client session
    async with aiohttp.ClientSession() as session:
        # Wrap the coroutines as Future objects and put them into a list.
        # Then, pass the list as tasks to be run.
        tasks = []
        for course in courses_to_search:
            task = asyncio.ensure_future(fetch(session, start_url, course, course.split(' ')[0], course.split(' '), 0))
            #print(course)
            tasks.append(task)

        await asyncio.gather(*tasks)

if __name__ == '__main__':
    parser = parser()
    cmd_args = parser.parse_args()
    print(cmd_args)
    validate_cmd_args(cmd_args)

    if has_sms_option:
        client = Client(secret_id, twilio_auth_token)

    if has_email_option:
        email_server = smtplib.SMTP('smtp.gmail.com', 587)
        email_server.starttls()
        email_server.login(email_sender, email_password)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())

    if email_server is not None:
        email_server.quit()
