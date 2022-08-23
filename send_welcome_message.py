from WelcomeMessage import WelcomeMessage


def send_welcome_message(client, channel, user, welcome_messages):  # welcome msg tracker
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
