#!/usr/bin/env python3

version = "0.1.0"

import os
from flask import Flask, request


class Config(object):
    clientID: str
    clientSecret: str

    def __init__(self) -> None:
        if (clientID := os.environ.get("EXAMPLE_CLIENT_ID")) is None:
            print("couldn't load EXAMPLE_CLIENT_ID")
            exit(1)
        elif (clientSecret := os.environ.get("EXAMPLE_CLIENT_SECRET")) is None:
            print("couldn't load EXAMPLE_CLIENT_SECRET")
            exit(1)

        self.clientID = clientID
        self.clientSecret = clientSecret


def authUrl(config: Config) -> str:
    return "&".join(
        [
            f"https://id.twitch.tv/oauth2/authorize?client_id={config.clientID}",
            f"client_secret={config.clientSecret}",
            "redirect_uri=http://localhost:8080/oauth2/subscribe",
            "grant_type=client_credentials",
            "response_type=code",
            "scopes=channel:read:predictions",
        ]
    )


config = Config()
urlWarning = f"""
Visit this url to authorize your Twitch Application to subscribe to your Twitch Account:

{authUrl(config)}

(Do not share this URL with others!)
"""

app = Flask(__name__)
app.logger.warning(urlWarning)


@app.route("/oauth2/subscribe")
def subscribe():
    app.logger.warning("creating subscription")
    # TODO: submit request to create subscription
    # https://dev.twitch.tv/docs/eventsub/eventsub-subscription-types#channelpredictionbegin
    # {
    #     "type": "channel.prediction.begin",
    #     "version": "1",
    #     "condition": {
    #         "broadcaster_user_id": "1337"
    #     },
    #     "transport": {
    #         "method": "webhook",
    #         "callback": "https://example.com/webhooks/callback",
    #         "secret": "s3cRe7"
    #     }
    # }
    pass
