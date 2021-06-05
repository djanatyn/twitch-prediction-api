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
    clientUsername: str


def loadConfig(app: Flask) -> Optional[Config]:
    """
    Construct Config from environment variables

    You should define:
    - EXAMPLE_CLIENT_ID
    - EXAMPLE_CLIENT_SECRET
    - EXAMPLE_CLIENT_USERNAME
    """
    if clientID := os.environ.get("EXAMPLE_CLIENT_ID") is None:
        app.logger.fatal("couldn't load EXAMPLE_CLIENT_ID")
    elif secret := os.environ.get("EXAMPLE_CLIENT_SECRET") is None:
        app.logger.fatal("couldn't load EXAMPLE_CLIENT_SECRET")
    elif username := os.environ.get("EXAMPLE_CLIENT_USERNAME") is None:
        app.logger.fatal("couldn't load EXAMPLE_CLIENT_USERNAME")
    else:
        config = Config(clientID=clientID, clientSecret=secret, clientUsername=username)
        loginPrompt = f"""
        Visit this url to authorize your Twitch Application to subscribe to your Twitch Account:

        {authUrl(config)}

        (Do not share this URL with others!)
        """
        app.logger.warning(loginPrompt)
        return config

    return None


def authUrl(config: Config) -> str:
    """
    Construct authentication URL for OAuth client credentials flow.

    https://dev.twitch.tv/docs/authentication/getting-tokens-oauth/#oauth-client-credentials-flow
    """
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


def lookupUsername(config: Config, username: str):
    """
    Look up UserID given a username.

    https://dev.twitch.tv/docs/api/reference#get-users
    """
    url = "https://api.twitch.tv/helix/users"
    payload = {"login": username}
    return requests.get(url, params=payload)


def createSubscription(
    config: Config, subType: str, userID: str, callbackURL: str, secret: str, token: str
):
    """
    Create subscription using EventSub API.

    https://dev.twitch.tv/docs/eventsub
    """
    url = "https://api.twitch.tv/helix/eventsub/subscriptions"
    payload = {
        "type": subType,
        "version": "1",
        "condition": {"broadcaster_user_id": userID},
        "transport": {"method": "webhook", "callback": callbackURL, "secret": secret},
    }
    return requests.post(url, json=payload)


app = Flask(__name__)
app.debug = True
if config := loadConfig(app) is None:
    sys.exit(1)
else:

    @app.route("/oauth2/subscribe")
    def subscribe():
        app.logger.warning("creating subscription")
        code = request.args.get("code")
        return "received code"
