# OpenSeat

A self-hosted Python script that notifies you when a UBC course seat is available. 

## Usage
```bash
python3 ./main.py [-h] [-ep EMAIL_PASSWORD] [-er EMAIL_RECIPIENT]
                       [-es EMAIL_SENDER] [-sid SECRET_ID] [-sr SMS_RECIPIENT]
                       [-ss SMS_SENDER] [-t TOKEN]


```
## Requirements
- Python 3.5+
- Twilio for SMS

## Crontab / Frequency
- You can use crontab to run the script as frequently as you like

## Restrictions
- Course names must have EXACTLY 3 words
    - Ex. ASTR 101 101
- Only supports popular email services (such as hotmail, gmail and yahoo). Feel free to add in your own SMTP address

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
- The email provider's SMTP servers often limit the number of emails you can send out. If you send out too many, your account may be blocked.

### Gmail
- You have to allow 'less secure apps' on your gmail account in your security settings.
- If you have two factor authentication, you will need a generated app password. Replace the password argument with the generated app password.


## TODO
- differentiate between blocked, restricted and general seats
