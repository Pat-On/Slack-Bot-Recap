import slack
import os
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, request, Response
from slackeventsapi import SlackEventAdapter
from WelcomeMessage import WelcomeMessage

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


def send_welcome_message(channel, user):  # welcome msg tracker
    welcome = WelcomeMessage(channel, user)
    message = welcome.get_message()
    # ** <- unpack operator for dictionaries
    response = client.chat_postMessage(**message)
    welcome.timestamp = response['ts']

    if channel not in welcome_messages:
        welcome_messages[channel] = {}
    welcome_messages[channel][user] = welcome


@slack_event_adapter.on('message')
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


@slack_event_adapter.on('reaction_added')
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


@app.route('/ message-count', methods=['POST'])
def message_count():
    data = request.form
    user_id = data.get('user_id')
    channel_id = data.get('channel_id')

    message_count = message_counts.get(user_id, 0)
    client.chat_postMessage(
        channel=channel_id, text=f'Messages: {message_count}')
    return Response(), 200


if __name__ == '__main__':
    app.run(debug=True)
