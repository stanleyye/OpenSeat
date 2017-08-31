#!/usr/bin/env python3

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

# BeautifulSoup parser type
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

def parser():
    """
    Creates a command argument parser with specified flags.

    Returns:
        the created parser.
    """
    parser = argparse.ArgumentParser(description='Get notified when a UBC course seat is available')
    parser.add_argument('-ep', '--email_password', type=str, help='Your email password')
    parser.add_argument('-er', '--email_recipient', type=str, help='The email address to send a notification to')
    parser.add_argument('-es', '--email_sender', type=str, help='The email address of the sender')
    parser.add_argument('-sid', '--secret_id', type=str, help='Your Twilio account\'s secret ID')
    parser.add_argument('-sr', '--sms_recipient', type=str, help='The phone number to receive the SMS message')
    parser.add_argument('-ss', '--sms_sender', type=str, help='Your Twilio-managed phone number')
    parser.add_argument('-t', '--token', type=str, help='Your Twilio authentication token')
    return parser

def read_course_file(file):
    """
    Reads the courses in the specified course file and adds it to a list of
    course names.

    Args:
        file: the specified course file.
    """
    with file.open() as f:
        for line in f:
            # if line is empty, continue
            if not line:
                continue

            # normalize the string to upper case + trimmed
            course = line.replace('\n', '').strip().upper()
            courses_to_search.append(course)

def select_smtp_address(email):
    """
    Select the right SMTP server address based on a specified email.

    Args:
        email: The specified email.
    Returns:
        the SMTP server address.
    """
    split_email = email.split('@')
    email_domain = split_email[1].lower()

    return {
        'aol.com': 'smtp.aol.com',
        'comcast.net': 'smtp.comcast.net',
        'gmail.com': 'smtp.gmail.com',
        'hotmail.com': 'smtp.live.com',
        'live.ca': 'smtp.live.com',
        'live.com': 'smtp.live.com',
        'outlook.com': 'smtp.live.com',
        'verizon.net': 'outgoing.verizon.net',
        'yahoo.com': 'mail.yahoo.com',
    }.get(email_domain, '')

def validate_cmd_args(cmd_args):
    """
    Validates the command arguments.

    Args:
        cmd_args: the command arguments.
    Raises:
        ValueError: if command arguments are missing.
    """
    email_args_count = 0

    if 'email_password' in cmd_args and cmd_args.email_password:
        email_args_count += 1

    if 'email_recipient' in cmd_args and cmd_args.email_recipient:
        email_args_count += 1

    if 'email_sender' in cmd_args and cmd_args.email_sender:
        email_args_count += 1

    if email_args_count == 3:
        global has_email_option, email_password, email_recipient, email_sender
        has_email_option = True
        email_password = cmd_args.email_password
        email_recipient = cmd_args.email_recipient
        email_sender = cmd_args.email_sender
    elif email_args_count > 0 and email_args_count < 3:
        raise ValueError('One or more of the following arguments are missing: email password, sender or recipient')

    sms_args_count = 0

    if 'secret_id' in cmd_args and cmd_args.secret_id:
        sms_args_count += 1

    if 'sms_recipient' in cmd_args and cmd_args.sms_recipient:
        sms_args_count += 1

    if 'sms_sender' in cmd_args and cmd_args.sms_sender:
        sms_args_count += 1

    if 'token' in cmd_args and cmd_args.token:
        sms_args_count += 1

    if sms_args_count == 4:
        global has_sms_option, secret_id, sms_recipient, sms_sender, twilio_auth_token
        has_sms_option = True
        secret_id = cmd_args.secret_id
        sms_recipient = cmd_args.sms_recipient
        sms_sender = cmd_args.sms_sender
        twilio_auth_token = cmd_args.token
    elif sms_args_count > 0 and sms_args_count < 4:
        raise ValueError('Missing either the Twilio auth token, Twio Secret ID, SMS Sender or the SMS Recipient')

    if email_args_count == 0 and sms_args_count == 0:
        raise ValueError('No command arguments specified.')

async def crawl():
    """
    Create an asyncio task for every course specified in courses.txt
    """

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

async def fetch(session, url, course, text_to_find, course_name_split, count):
    """
    Gets the returned HTML from the response and parses it.

    Args:
        session: the aiohttp client session
        url: the url to fetch (send a HTTP GET request to)
        course: the course name
        text_to_find: The text value to look for in the HTML
        course_name_split: A list that consists of the split course name
        count: a number to keep track of how many links traversed
    """

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
    """
    Sends an email.

    Args:
        course: The specified course (email subject)
    """
    msg = MIMEMultipart()
    msg['From'] = email_sender
    msg['To'] = email_recipient
    msg['Subject'] = 'OpenSeat - {}'.format(course)

    body = 'There is an open seat in {}.'.format(course)
    msg.attach(MIMEText(body,'plain'))

    msg_text = msg.as_string()
    email_server.sendmail(email_sender, email_recipient, msg_text)

async def send_sms(course):
    """
    Sends a SMS message.

    Args:
        course: The specified course (SMS subject)
    """
    client.messages.create(
        to=sms_recipient,
        from_=sms_sender,
        body='A spot is available in {}.'.format(course)
    )

def main():
    """
    Main function. Initializes and sets up the variables for the program.
    """

    # Set up the parser
    cmd_parser = parser()
    cmd_args = cmd_parser.parse_args()
    print(cmd_args)

    # Validate command arguments
    validate_cmd_args(cmd_args)

    if has_sms_option:
        global client
        client = Client(secret_id, twilio_auth_token)

    if has_email_option:
        global email_server
        email_server = smtplib.SMTP(
            select_smtp_address(email_sender),
            587
        )
        email_server.starttls()
        email_server.login(email_sender, email_password)

    courses = Path('./courses.txt')

    # Check whether courses.txt is defined
    if not courses.is_file():
        print('courses.txt does not exist.')
        return

    # Read the file and put the courses into a list
    read_course_file(courses)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(asyncio.ensure_future(crawl()))

    if email_server is not None:
        email_server.quit()

if __name__ == '__main__':
    main()
