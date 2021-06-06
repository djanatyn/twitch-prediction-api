# twitch-prediction-api

Example python code creating a subscription using Twitch's Channel Prediction APIs.

Logs predictions from a stream in real-time.

Implemented using flask.

# usage

## requirements

You'll need:
- a [Twitch application](https://https://dev.twitch.tv/console/apps) (to make API requests),
- and an HTTPS callback URL (to recieve EventSub events),

If you don't have an HTTPS url easily available, Twitch recommends using [ngrok](https://ngrok.com):

> The URL provided in the callback field MUST use HTTPS and port 443. For local development consider using a product like ngrok to easily create an HTTPS endpoint.

## application setup

Set the OAuth redirect URL to: `http://localhost:8000/oauth2/subscribe`.

Create a new client secret.

## server startup

Start the server:
```bash
export EXAMPLE_CLIENT_ID="..."
export EXAMPLE_CLIENT_SECRET="..."
export EXAMPLE_CLIENT_USERNAME="..."
export EXAMPLE_CALLBACK_URL="..."
export FLASK_APP=twitch_prediction_api_example

poetry install
poetry run python -m flask run -p 8000
```

## authorize application to read predictions on account

Follow the link to authorize (`channel:read:predictions`) your *Twitch Application* with your *Twitch Account*:
```
[2021-06-04 00:17:50,348] WARNING in __init__:
Visit this url to authorize your Twitch Application to subscribe to your Twitch Account:

https://id.twitch.tv/oauth2/authorize?client_id=...&client_secret=...&redirect_uri=http://localhost:8080/oauth2/subscribe&grant_type=client_credentials&response_type=code&scopes=channel:read:predictions

(Do not share this URL with others!)
```

If successful, the application will redirect to the `/oauth2/subscribe` endpoint, which will trigger subscription creation:
```
[2021-06-05 22:57:06,759] WARNING in __init__: retrieving access token
[2021-06-05 22:57:07,262] WARNING in __init__: <access token>
[2021-06-05 22:57:07,452] WARNING in __init__: <user ID>
[2021-06-05 22:57:07,957] WARNING in __init__: <oauth client credential token>
[2021-06-05 22:57:07,957] INFO in __init__: SubscriptionRequest(subtype='channel.prediction.begin', userID='...', callbackURL='https://6f638ef14d5e.ngrok.io/callbacks/eventsub', secret='...', token='...')
[2021-06-05 22:57:08,180] WARNING in __init__: {'data': [{'id': '3fe85516-6e09-4dee-9a27-0a3bf6685bcc', 'status': 'webhook_callback_verification_pending', 'type': 'channel.prediction.begin', 'version': '1', 'condition': {'broadcaster_user_id': '...'}, 'created_at': '2021-06-06T02:57:08.111041061Z', 'transport': {'method': 'webhook', 'callback': 'https://...'}, 'cost': 0}], 'total': 5, 'max_total_cost': 10000, 'total_cost': 0}
127.0.0.1 - - [05/Jun/2021 22:57:08] "GET /oauth2/subscribe?code=...&scope=channel%3Aread%3Apredictions+user%3Aread%3Aemail HTTP/1.1" 200 -
[2021-06-05 22:57:09,303] INFO in __init__: eventsub request
[2021-06-05 22:57:09,303] WARNING in __init__: <Request 'http://.../callbacks/eventsub' [POST]>
[2021-06-05 22:57:09,303] WARNING in __init__: {'subscription': {'id': '3fe85516-6e09-4dee-9a27-0a3bf6685bcc', 'status': 'webhook_callback_verification_pending', 'type': 'channel.prediction.begin', 'version': '1', 'condition': {'broadcaster_user_id': '...'}, 'transport': {'method': 'webhook', 'callback': 'https://.../callbacks/eventsub'}, 'created_at': '2021-06-06T02:57:08.111041061Z', 'cost': 0}, 'challenge': '...'}
127.0.0.1 - - [05/Jun/2021 22:57:09] "POST /callbacks/eventsub HTTP/1.1" 200 -
```

# development

```bash
export EXAMPLE_CLIENT_ID="$(pass show twitch.tv/prediction-api-bot/client-id)"
export EXAMPLE_CLIENT_SECRET="$(pass show twitch.tv/prediction-api-bot/client-secret)"
export EXAMPLE_CLIENT_USERNAME="my_twitch_username"
export EXAMPLE_CALLBACK_URL="https://my-ngrok-url/callbacks/eventsub"

poetry install

ls twitch_prediction_api_example/*.py \
  | FLASK_APP=twitch_prediction_api_example \
  entr -r poetry run python -m flask run -p 8080
```

# reference
- [initial announcement](https://discuss.dev.twitch.tv/t/announcing-apis-and-eventsub-for-polls-and-predictions/31539)
- [eventsub](https://dev.twitch.tv/docs/eventsub/eventsub-subscription-types#channelpollbegin-beta)

# also see
- [streamcord/spyglass](https://github.com/streamcord/spyglass)
