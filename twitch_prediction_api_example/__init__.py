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
    callbackURL: str
    username: str


def loadConfig(app: Flask) -> Optional[Config]:
    """
    Construct Config from environment variables

    You should define:
    - EXAMPLE_CLIENT_ID
    - EXAMPLE_CLIENT_SECRET
    - EXAMPLE_CLIENT_USERNAME
    - EXAMPLE_CALLBACK_URL
    """
    if (clientID := os.environ.get("EXAMPLE_CLIENT_ID")) is None:
        app.logger.fatal("couldn't load EXAMPLE_CLIENT_ID")
    elif (clientSecret := os.environ.get("EXAMPLE_CLIENT_SECRET")) is None:
        app.logger.fatal("couldn't load EXAMPLE_CLIENT_SECRET")
    elif (username := os.environ.get("EXAMPLE_CLIENT_USERNAME")) is None:
        app.logger.fatal("couldn't load EXAMPLE_CLIENT_USERNAME")
    elif (callbackURL := os.environ.get("EXAMPLE_CALLBACK_URL")) is None:
        app.logger.fatal("couldn't load EXAMPLE_CALLBACK_URL")
    else:
        config = Config(
            clientID=clientID,
            clientSecret=clientSecret,
            callbackURL=callbackURL,
            username=username,
        )
        loginPrompt = "\n\n".join(
            [
                "Visit this url to authorize your Twitch Application to subscribe to your Twitch Account:",
                authCodeFlowUrl(config),
                "(Do not share this URL with others!)",
            ]
        )
        app.logger.warning(loginPrompt)
        return config

    return None


def authCodeFlowUrl(config: Config) -> str:
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
    token: str


def requestSubscription(config: Config, sub: SubscriptionRequest):
    """
    Create subscription using EventSub API.

    https://dev.twitch.tv/docs/eventsub
    """
    url = "https://api.twitch.tv/helix/eventsub/subscriptions"
    headers = {
        "Authorization": f"Bearer {sub.token}",
        "Client-ID": config.clientID,
        "Content-Type": "application/json",
    }
    payload = {
        "type": sub.subtype,
        "version": "1",
        "condition": {"broadcaster_user_id": sub.userID},
        "transport": {
            "method": "webhook",
            "callback": sub.callbackURL,
            "secret": sub.secret,
        },
    }
    return requests.post(url, json=payload, headers=headers)


def oauthClientCredentials(config: Config) -> requests.Response:
    url = "https://id.twitch.tv/oauth2/token"
    payload = {
        "client_id": config.clientID,
        "client_secret": config.clientSecret,
        "grant_type": "client_credentials",
        "scope": "channel:read:predictions user:read:email",
    }
    return requests.post(url, params=payload)


app = Flask(__name__)
app.debug = True

if (config := loadConfig(app)) is None:
    sys.exit(1)
else:

    @app.route("/oauth2/subscribe")
    def subscribe():
        # oauth authorization code flow
        app.logger.warning("retrieving access token")
        code = request.args.get("code")
        # get access token with authorization code
        tokenResponse = requestAccessToken(config, code)
        assert tokenResponse.status_code == 200
        app.logger.warning(userAccessToken := tokenResponse.json().get("access_token"))

        # look up userID with access token
        usernameResponse = lookupUsername(config, userAccessToken)
        assert usernameResponse.status_code == 200
        app.logger.warning(userID := usernameResponse.json()["data"][0]["id"])

        # request oauth client credential token
        clientCredsRepsonse = oauthClientCredentials(config)
        assert clientCredsRepsonse.status_code == 200
        app.logger.warning(
            clientCredToken := clientCredsRepsonse.json().get("access_token")
        )

        subRequest = SubscriptionRequest(
            subtype="channel.prediction.begin",
            userID=userID,
            callbackURL=config.callbackURL,
            secret="changemechangeme",
            token=clientCredToken,
        )
        app.logger.info(subRequest)
        response = requestSubscription(config, subRequest)
        app.logger.warning(response.json())

        return "requested subscription!"
