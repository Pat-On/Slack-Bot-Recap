import datetime

# message counter - normally it would be DB
message_counts = {}
welcome_messages = {}

# data used in demo

timer = (datetime.datetime.now() +
         datetime.timedelta(seconds=30)).strftime('%s')

SCHEDULED_MESSAGES = [
    {'text': 'First message', 'post_at': timer, 'channel': 'C03UJD84DFB'},
    {'text': 'Second Message!', 'post_at': timer, 'channel': 'C03UJD84DFB'}
]
