#!/usr/bin/env python3

version = "0.1.0"

import os
import sys
import requests
from dataclasses import dataclass
from typing import Optional
from flask import Flask, request


@dataclass
class Config:
    clientID: str
    clientSecret: str
    username: str


def loadConfig(app: Flask) -> Optional[Config]:
    """
    Construct Config from environment variables

    You should define:
    - EXAMPLE_CLIENT_ID
    - EXAMPLE_CLIENT_SECRET
    - EXAMPLE_CLIENT_USERNAME
    """
    if (clientID := os.environ.get("EXAMPLE_CLIENT_ID")) is None:
        app.logger.fatal("couldn't load EXAMPLE_CLIENT_ID")
    elif (clientSecret := os.environ.get("EXAMPLE_CLIENT_SECRET")) is None:
        app.logger.fatal("couldn't load EXAMPLE_CLIENT_SECRET")
    elif (username := os.environ.get("EXAMPLE_CLIENT_USERNAME")) is None:
        app.logger.fatal("couldn't load EXAMPLE_CLIENT_USERNAME")
    else:
        config = Config(clientID, clientSecret, username)
        loginPrompt = "\n\n".join(
            [
                "Visit this url to authorize your Twitch Application to subscribe to your Twitch Account:",
                authUrl(config),
                "(Do not share this URL with others!)",
            ]
        )
        app.logger.warning(loginPrompt)
        return config

    return None


def authUrl(config: Config) -> str:
    """
    Construct authentication URL for OAuth authorization code flow.

    https://dev.twitch.tv/docs/authentication/getting-tokens-oauth/#oauth-authorization-code-flow
    """
    return "&".join(
        [
            f"https://id.twitch.tv/oauth2/authorize?client_id={config.clientID}",
            f"client_secret={config.clientSecret}",
            "redirect_uri=http://localhost:8080/oauth2/subscribe",
            "grant_type=client_credentials",
            "response_type=code",
            "scope=channel:read:predictions%20user:read:email",
        ]
    )


def lookupUsername(config: Config, token: str) -> requests.Response:
    """
    Look up UserID given a username.

    https://dev.twitch.tv/docs/api/reference#get-users
    """
    url = "https://api.twitch.tv/helix/users"
    payload = {"login": config.username}
    headers = {"Authorization": f"Bearer {token}", "Client-Id": config.clientID}
    return requests.get(url, params=payload, headers=headers)


def requestAccessToken(config: Config, code: str) -> requests.Response:
    """
    Use code to retrieve access token in OAuth authorization code flow.

    https://dev.twitch.tv/docs/eventsub
    """
    url = "https://id.twitch.tv/oauth2/token"
    payload = {
        "client_id": config.clientID,
        "client_secret": config.clientSecret,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": "http://localhost:8080/oauth2/subscribe",
    }
    return requests.post(url, params=payload)


@dataclass
class SubscriptionRequest:
    """
    Used to construct requests for EventSub subscriptions.
    """

    subtype: str
    userID: str
    callbackURL: str
    secret: str


def requestSubscription(config: Config, sub: SubscriptionRequest, token: str):
    """
    Create subscription using EventSub API.

    https://dev.twitch.tv/docs/eventsub
    """
    url = "https://api.twitch.tv/helix/eventsub/subscriptions"
    payload = {
        "type": sub.subType,
        "version": "1",
        "condition": {"broadcaster_user_id": sub.userID},
        "transport": {
            "method": "webhook",
            "callback": sub.callbackURL,
            "secret": sub.secret,
        },
    }
    return requests.post(url, json=payload)


app = Flask(__name__)
app.debug = True

if (config := loadConfig(app)) is None:
    sys.exit(1)
else:

    @app.route("/oauth2/subscribe")
    def subscribe():
        app.logger.warning("retrieving access token")
        code = request.args.get("code")
        tokenResponse = requestAccessToken(config, code)
        app.logger.warning(token := tokenResponse.json().get("access_token"))

        usernameResponse = lookupUsername(config, token)
        app.logger.warning(usernameResponse.json())

        #     request = SubscriptionRequest(
        #         subtype="channel.prediction.begin",
        #         userID=
        #         callbackURL="http://localhost:8080/subscribe"
        # secret: str
        #     )
        #     createSubscription(config, SubscriptionRequest())
        return "received code"
