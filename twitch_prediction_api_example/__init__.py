#!/usr/bin/env python3


version = "0.1.0"

import os
import sys
import requests
from dataclasses import dataclass
from typing import Optional
from flask import Flask, request


@dataclass
class ClientCredentials:
    """
    client_id and client_secret.

    These are provided by Twitch when creating your app on dev.twitch.tv.
    """

    clientID: str
    clientSecret: str


@dataclass
class Config:
    """
    Application configuration:
    - client credentials from a Twitch app,
    - FQDN of running server,
    - Username to register event subscriptions for.
    """

    creds: ClientCredentials
    callbackBaseURL: str
    username: str


@dataclass
class UserAccessToken:
    """
    Token granted after the user successfully authorizes permissions to the app.

    Can be used to lookup userID given a username, using Twitch's Helix API.
    userIDs are required for creating subscriptions.

    > Authenticate users and allow your app to make requests on their behalf. If
      your application uses Twitch for login or makes requests in the context of
      an authenticated user, you need to generate a user access token.
    """

    token: str


def loadConfig(app: Flask) -> Optional[Config]:
    """
    Construct Config from environment variables.

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
    elif (callbackBaseURL := os.environ.get("EXAMPLE_CALLBACK_BASE_URL")) is None:
        app.logger.fatal("couldn't load EXAMPLE_CALLBACK_BASE_URL")
    else:
        config = Config(
            creds=ClientCredentials(
                clientID=clientID,
                clientSecret=clientSecret,
            ),
            callbackBaseURL=callbackBaseURL,
            username=username,
        )
        loginPrompt = "\n\n".join(
            [
                "Visit this url to authorize your Twitch Application to subscribe to your Twitch Account:",
                authCodeFlowUrl(config.callbackBaseURL, config.creds.clientID),
            ]
        )
        app.logger.warning(loginPrompt)
        return config

    return None


def authCodeFlowUrl(callbackBaseURL: str, clientID: str) -> str:
    """
    Construct authentication URL for OAuth authorization code flow.

    Send this to the user you want to subscribe to. They'll give permission to
    authorize your Twitch application.

    https://dev.twitch.tv/docs/authentication/getting-tokens-oauth/#oauth-authorization-code-flow
    """
    return "&".join(
        [
            f"https://id.twitch.tv/oauth2/authorize?client_id={clientID}",
            f"redirect_uri={callbackBaseURL}/oauth2/subscribe",
            "response_type=code",
            "scope=channel:read:predictions%20user:read:email",
        ]
    )


# def lookupSubscriptions(config: Config, token: str): -> requests.Response:
#     """
#     """


def lookupUsername(username: str, token: str) -> requests.Response:
    """
    Look up UserID given a username (from Config).
    Uses user access token.

    https://dev.twitch.tv/docs/api/reference#get-users
    """
    url = "https://api.twitch.tv/helix/users"
    payload = {"login": username}
    headers = {"Authorization": f"Bearer {token}", "Client-Id": config.creds.clientID}
    return requests.get(url, params=payload, headers=headers)


def requestAccessToken(creds: ClientCredentials, code: str) -> requests.Response:
    """
    Use code from Twitch to acquire user access token in OAuth authorization code flow.

    https://dev.twitch.tv/docs/eventsub
    """
    url = "https://id.twitch.tv/oauth2/token"
    payload = {
        "client_id": creds.clientID,
        "client_secret": creds.clientSecret,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": "http://localhost:8080/oauth2/subscribe",
    }
    return requests.post(url, params=payload)


def oauthClientCredentials(creds: ClientCredentials) -> requests.Response:
    """
    Request app access token with the following scopes:
    - channel:read:predictions
    - user:read:email

    https://dev.twitch.tv/docs/authentication/getting-tokens-oauth/#oauth-client-credentials-flow

    > As mentioned earlier, app access tokens are only for server-to-server API
      requests. The grant request below requires the client secret to acquire an
      app access token; this also should be done only as a server-to-server
      request, never in client code.
    """
    url = "https://id.twitch.tv/oauth2/token"
    payload = {
        "client_id": creds.clientID,
        "client_secret": creds.clientSecret,
        "grant_type": "client_credentials",
        "scope": "channel:read:predictions user:read:email",
    }
    return requests.post(url, params=payload)


@dataclass
class SubscriptionRequest:
    """
    Used to construct requests for EventSub subscriptions.
    """

    subtype: str
    userID: str
    secret: str
    token: str


def requestSubscription(clientID: str, callbackBaseURL: str, sub: SubscriptionRequest):
    """
    Create subscription using EventSub API.

    https://dev.twitch.tv/docs/eventsub
    """
    url = "https://api.twitch.tv/helix/eventsub/subscriptions"
    headers = {
        "Authorization": f"Bearer {sub.token}",
        "Client-ID": clientID,
        "Content-Type": "application/json",
    }
    payload = {
        "type": sub.subtype,
        "version": "1",
        "condition": {"broadcaster_user_id": sub.userID},
        "transport": {
            "method": "webhook",
            "callback": f"{callbackBaseURL}/callbacks/eventsub",
            "secret": sub.secret,
        },
    }
    return requests.post(url, json=payload, headers=headers)


app = Flask(__name__)
app.debug = True

if (config := loadConfig(app)) is None:
    sys.exit(1)
else:

    @app.route("/oauth2/subscribe", methods=["GET", "POST"])
    def subscribe():
        """
        Subscription endpoint for OAuth.

        Requests come from Twitch, after a user approves permissions.
        Twitch sends a code, which is used to acquire a user access token.

        """
        # oauth authorization code flow
        app.logger.warning("retrieving access token")
        code = request.args.get("code")

        # get access token with authorization code
        tokenResponse = requestAccessToken(config.creds, code)
        assert tokenResponse.status_code == 200
        app.logger.warning(userAccessToken := tokenResponse.json().get("access_token"))

        # look up userID with access token
        usernameResponse = lookupUsername(config.username, userAccessToken)
        assert usernameResponse.status_code == 200
        app.logger.warning(userID := usernameResponse.json()["data"][0]["id"])

        # request oauth client credential token
        clientCredsRepsonse = oauthClientCredentials(config.creds)
        assert clientCredsRepsonse.status_code == 200
        app.logger.warning(
            clientCredToken := clientCredsRepsonse.json().get("access_token")
        )

        # request subscription
        subRequest = SubscriptionRequest(
            subtype="channel.prediction.begin",
            userID=userID,
            secret="changemechangeme",
            token=clientCredToken,
        )
        app.logger.info(subRequest)
        response = requestSubscription(
            config.creds.clientID, config.callbackBaseURL, subRequest
        )
        app.logger.warning(response.json())

        return "requested subscription!"

    @app.route("/callbacks/eventsub", methods=["POST"])
    def eventsub():
        app.logger.info("eventsub request")
        app.logger.warning(request.json)

        app.logger.warning(challenge := request.json.get("challenge"))
        assert challenge is not None

        return request.json.get(challenge)
