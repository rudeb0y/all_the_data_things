import requests

from prefect import task, flow, get_run_logger

from prefect_slack import SlackCredentials
from prefect_slack.messages import send_chat_message
from prefect.blocks.system import Secret


# Extraction Task pulls 5-day, 3-hour forcast for the provided City
@task(retries=2, retry_delay_seconds=5)
def pull_forecast(city, api_key):
    base_url = "http://api.openweathermap.org/data/2.5/forecast?"
    url = base_url + "appid=" + api_key + "&q=" + city
    r = requests.get(url)
    r.raise_for_status()
    data = r.json()
    return data


@task(tags=["example", "api", "weather"])
def is_raining_this_week(data):
    rain = [
        forecast["rain"].get("3h", 0) for forecast in data["list"] if "rain" in forecast
    ]
    return True if sum([s >= 1 for s in rain]) >= 1 else False


# Notification Task sends message to Cloud once authenticated with a webhook
rain_notification, dry_notification = [
    """🎵 Raindrops keep fallin' on my head, and just like the guy whose feet are too big for his bed,
 I'm never gonna stop the rain by complainin' 🌧️☂️ """,
    "🎤 It's gonna be a bright (bright) Bright (bright) sunshiny day! 🎵🌻😎",
]


@flow
def rain_flow(city: str = "Birmingham"):
    logger = get_run_logger()

    api_key = Secret.load("openweathermap-api-key")
    slack_credentials = SlackCredentials.load("allthedatathings")

    forecast = pull_forecast(city=city, api_key=api_key.get())
    rain = is_raining_this_week(forecast)

    message = rain_notification if rain else dry_notification

    logger.info(f"Sending slack message: { message }")

    send_chat_message(
        slack_credentials=slack_credentials, channel="#sandbox", text=message
    )


if __name__ == "__main__":
    rain_flow(city="Texas")
