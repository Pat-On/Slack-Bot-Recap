import slack
import os
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, request, Response
from slackeventsapi import SlackEventAdapter
import scheduler
from bad_words import check_if_bad_words
from send_welcome_message import send_welcome_message
from demo_data import message_counts, welcome_messages, SCHEDULED_MESSAGES

import pprint
printer = pprint.PrettyPrinter()

# change the link in the Slash Commands and enable events slack API - ngrok

# CONFIG #####################################################
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

app = Flask(__name__)
slack_event_adapter = SlackEventAdapter(
    os.environ['SIGNING_SECRET'], '/slack/events', app)

client = slack.WebClient(token=os.environ['SLACK_TOKEN'])
BOT_ID = client.api_call('auth.test')['user_id']

###############################################################


@ slack_event_adapter.on('message')
# catching event 'message'
def message(payload):
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
            send_welcome_message(
                client, f'@{user_id}', user_id, welcome_messages)
            # catching commands
        elif check_if_bad_words(text):
            # time stamp is to nanoseconds and they are using it as an id of the msg
            ts = event.get('ts')
            client.chat_postMessage(
                channel=channel_id, thread_ts=ts, text="That is bad word!")
            # client.chat_delete(channel=channel_id, ts=ts)


@ slack_event_adapter.on('reaction_added')
# You need to go to Event Subscriptions -> Subscribe to bot events and add in that case reaction_added
def reaction(payload):
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
    scheduler.schedule_messages(client, SCHEDULED_MESSAGES)
    ids = scheduler.list_scheduled_messages(client, 'C03UJD84DFB')
    # scheduler.delete_scheduled_messages(
    #     client, ids, "C03UJD84DFB")  # <- wrong ids
    app.run(debug=True)
