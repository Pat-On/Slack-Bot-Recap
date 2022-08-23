import string
import slack
import os
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, request, Response
from slackeventsapi import SlackEventAdapter
from WelcomeMessage import WelcomeMessage
# from datetime import datetime, timedelta
import datetime

import pprint

printer = pprint.PrettyPrinter()

# change the link in the Slash Commands and enable events slack API - ngrok

# loading token
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)


app = Flask(__name__)
slack_event_adapter = SlackEventAdapter(
    os.environ['SIGNING_SECRET'], '/slack/events', app)

client = slack.WebClient(token=os.environ['SLACK_TOKEN'])
BOT_ID = client.api_call('auth.test')['user_id']

# client.chat_postMessage(channel='#test', text='Hello World!')

# message counter - normally it would be DB
message_counts = {}

welcome_messages = {}

BAD_WORDS = ["hmm", "guys"]

timer = (datetime.datetime.now() +
         datetime.timedelta(seconds=30)).strftime('%s')

SCHEDULED_MESSAGES = [
    {'text': 'First message', 'post_at': timer, 'channel': 'C03UJD84DFB'},
    {'text': 'Second Message!', 'post_at': timer, 'channel': 'C03UJD84DFB'}
]


def send_welcome_message(channel, user):  # welcome msg tracker
    if channel not in welcome_messages:
        welcome_messages[channel] = {}

    if user in welcome_messages[channel]:
        return

    welcome = WelcomeMessage(channel, user)
    message = welcome.get_message()
    # ** <- unpack operator for dictionaries
    response = client.chat_postMessage(**message)
    welcome.timestamp = response['ts']

    welcome_messages[channel][user] = welcome


def schedule_messages(messages):
    ids = []
    for msg in messages:
        response = client.chat_scheduleMessage(
            channel=msg['channel'], text=msg['text'], post_at=msg['post_at']).data
        # printer.pprint(response)
        id_ = response.get('scheduled_message_id')
        ids.append(id_)

    return ids


def list_scheduled_messages(channel):
    response = client.chat_scheduledMessages_list(channel=channel)
    messages = response.data.get('scheduled_messages')
    ids = []
    for msg in messages:
        ids.append(msg.get('id'))

    return ids


def delete_scheduled_messages(ids, channel):
    for _id in ids:
        try:
            client.chat_deleteScheduledMessage(
                channel=channel, scheduled_message_id=_id)
        except Exception as e:
            print(e)


def check_if_bad_words(message):
    msg = message.lower()
    msg = msg.translate(str.maketrans('', '', string.punctuation))

    return any(word in msg for word in BAD_WORDS)


@ slack_event_adapter.on('message')
def message(payload):  # catching event 'message'
    # print(payload)
    event = payload.get('event', {})
    channel_id = event.get('channel')
    user_id = event.get('user')
    text = event.get('text')
    if user_id != None and BOT_ID != user_id:
        if user_id in message_counts:
            message_counts[user_id] += 1
        else:
            message_counts[user_id] = 1
        # client.chat_postMessage(channel=channel_id, text=text)

        if text.lower() == 'start':
            # send_welcome_message(channel_id, user_id)

            # sending direct msg
            send_welcome_message(f'@{user_id}', user_id)
            # catching commands
        elif check_if_bad_words(text):
            # time stamp is to nanoseconds and they are using it as an id of the msg
            ts = event.get('ts')
            client.chat_postMessage(
                channel=channel_id, thread_ts=ts, text="That is bad word!")
            # client.chat_delete(channel=channel_id, ts=ts)


@ slack_event_adapter.on('reaction_added')
def reaction(payload):  # You need to go to Event Subscriptions -> Subscribe to bot events and add in that case reaction_added
    event = payload.get('event', {})
    # this payload is different so we need to change it
    channel_id = event.get('item', {}).get('channel')
    user_id = event.get('user')

    if f'@{user_id}' not in welcome_messages:
        return

    welcome = welcome_messages[f'@{user_id}'][user_id]
    welcome.completed = True

    # fix of error
    welcome.channel = channel_id

    message = welcome.get_message()
    updated_message = client.chat_update(**message)
    welcome.timestamp = updated_message['ts']


@ app.route('/message-count', methods=['POST'])
def message_count():
    data = request.form
    user_id = data.get('user_id')
    channel_id = data.get('channel_id')

    message_count = message_counts.get(user_id, 0)
    client.chat_postMessage(
        channel=channel_id, text=f'Messages: {message_count}')
    return Response(), 200


if __name__ == '__main__':
    schedule_messages(SCHEDULED_MESSAGES)
    ids = list_scheduled_messages('C03UJD84DFB')
    delete_scheduled_messages(ids, "C03UJD84DFB")  # <- wrong ids
    app.run(debug=True)
