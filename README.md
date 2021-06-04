# twitch-prediction-api

Example python code creating a subscription using Twitch's Channel Prediction APIs.

Logs predictions from a stream in real-time.

Implemented using flask.

# usage

First, create a [Twitch application](https://https://dev.twitch.tv/console/apps).
Set the OAuth redirect URL to: `http://localhost:8000/oauth2/subscribe`
Create a new client secret.

Start the server:
```bash
export EXAMPLE_CLIENT_ID="..."
export EXAMPLE_CLIENT_SECRET="..."
export FLASK_APP=twitch_prediction_api_example

poetry install
poetry run python -m flask run -p 8000
```

Follow the link to authorize (`channel:read:predictions`) your *Twitch Application* with your *Twitch Account*:
```
[2021-06-04 00:17:50,348] WARNING in __init__:
Visit this url to authorize your Twitch Application to subscribe to your Twitch Account:

https://id.twitch.tv/oauth2/authorize?client_id=...&client_secret=...&redirect_uri=http://localhost:8080/oauth2/subscribe&grant_type=client_credentials&response_type=code&scopes=channel:read:predictions

(Do not share this URL with others!)
```

If successful, the application will redirect to the `/oauth2/subscribe` endpoint, which will trigger subscription creation:
```
[2021-06-04 00:17:55,828] WARNING in __init__: creating subscription
127.0.0.1 - - [04/Jun/2021 00:17:55] "GET /oauth2/subscribe?code=...&scope= HTTP/1.1" 200 -
```

# development

```bash
export EXAMPLE_CLIENT_ID="$(pass show twitch.tv/prediction-api-bot/client-id)"
export EXAMPLE_CLIENT_SECRET="$(pass show twitch.tv/prediction-api-bot/client-secret)"

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
