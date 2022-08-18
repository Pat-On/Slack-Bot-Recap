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
