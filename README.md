# Disclaimer
This code is developed for educational purposes only and no abuse of any services, either Github, Spotify, or Telegram is instended.

# How to
* Create a telegram bot using [@BotFather](https://t.me/BotFather) and get your bot API token.
* Create an Actions Secret called `TELEGRAM_BOT_TOKEN` and set the value as your bot API token.
* Make sure you've allowed `Read and Write Permission` to github actions before running the workflow.
* To avoid extended workflow run for free users and avoid abuse of services, worfklows are set out to cancel the workflow after a limited time. Adjust it under `timeout-minutes`, capped at 6 hours due to Github policies (360 minutes).
* Run the workflow `Default` to get videos and playlist in default resolution.
* Run the workflow `Custom` to get videos and playlist in custom resolution.
