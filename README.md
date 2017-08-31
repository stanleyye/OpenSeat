# OpenSeat

This self-hosted script notifies you when a UBC course seat is available. 

## Usage
```bash
python3 ./main.py [-h] [-ep EMAIL_PASSWORD] [-er EMAIL_RECIPIENT]
                       [-es EMAIL_SENDER] [-sid SECRET_ID] [-sr SMS_RECIPIENT]
                       [-ss SMS_SENDER] [-t TOKEN]


```
## Requirements
- Python 3.5+
- Twilio for SMS

## Restrictions
- Course names must have EXACTLY 3 words
    - Ex. ASTR 101 101

## Options
    -h, --help                       Print this help text and exit
    -ep, --email_password            Your email password
    -er, --email_recipient           The email address to send a notification to
    -es, --email_sender              The email address of the sender
    -sid, --secret_id                Your Twio account's secret ID
    -sr, --sms_recipient             The phone number to receive the SMS message
    -ss, --sms_sender                Your Twilio-managed phone number
    -t, --token                      Your Twilio authentication token

## Email
### Gmail
- You have to allow 'less secure apps' on your gmail account in your security settings.
- If you have two factor authentication, you will need a generated app password. Replace the password argument with the generated app password.


## TODO
- differentiate between blocked, restricted and general seats
- set frequency of checking. The script currently only checks once. Crontab?
- support for other email services such as Hotmail or Yahoo
