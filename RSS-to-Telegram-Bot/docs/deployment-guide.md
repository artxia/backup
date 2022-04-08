# Deployment Guide

## Preparation

> For more env variables and detailed information, read [Advanced Settings](advanced-settings.md).

1. Turn to [@BotFather](https://t.me/BotFather), send `/newbot` create a new bot, then get its token (env variable: `TOKEN`). After that, send `/setinline`, select your bot, and reply with an inline placeholder you like to enable inline mode for your bot. For example, [@RSStT_Bot](https://t.me/RSStT_Bot) is using `Please input a command to continue...`.
2. Turn to [@userinfobot](https://t.me/userinfobot) to get your user ID (env variable: `MANAGER`).
3. [Get Telegraph API access tokens](https://api.telegra.ph/createAccount?short_name=RSStT&author_name=Generated%20by%20RSStT&author_url=https%3A%2F%2Fgithub.com%2FRongronggg9%2FRSS-to-Telegram-Bot) (env variable: `TELEGRAPH_TOKEN`). Refresh the page every time you get a new token. If you have a lot of subscriptions, make sure to get at least 5 tokens.

## Option 1: Docker Compose

[![Docker Image Size (tag)](https://img.shields.io/docker/image-size/rongronggg9/rss-to-telegram/latest?logo=docker)](https://hub.docker.com/r/rongronggg9/rss-to-telegram)
[![Build status (master)](https://img.shields.io/github/workflow/status/Rongronggg9/RSS-to-Telegram-Bot/Publish%20Docker%20image/master?label=build&logo=docker)](https://github.com/Rongronggg9/RSS-to-Telegram-Bot/actions/workflows/publish-docker-image.yml?query=branch%3Amaster)
[![Build status (dev)](https://img.shields.io/github/workflow/status/Rongronggg9/RSS-to-Telegram-Bot/Publish%20Docker%20image/dev?label=build%20%28dev%29&logo=docker)](https://github.com/Rongronggg9/RSS-to-Telegram-Bot/actions/workflows/publish-docker-image.yml?query=branch%3Adev)
[![Docker pulls](https://img.shields.io/docker/pulls/rongronggg9/rss-to-telegram?label=pulls&logo=docker&color=informational)](https://hub.docker.com/r/rongronggg9/rss-to-telegram)

For the docker images go to: https://hub.docker.com/r/rongronggg9/rss-to-telegram

### Deploy

```sh
mkdir rsstt
cd rsstt
wget https://raw.githubusercontent.com/Rongronggg9/RSS-to-Telegram-Bot/dev/docker-compose.yml.sample -O docker-compose.yml
vi docker-compose.yml  # fill in env variables
docker-compose up -d
```

### Update

```sh
docker-compose down
docker-compose pull
docker-compose up -d
```

## Option 2: Railway.app

### Deploy

> Uncheck the checkbox `Private repository`! Or you are not able to update with ease.

|                             master                              |                            dev                            |
|:---------------------------------------------------------------:|:---------------------------------------------------------:|
| [![Deploy on Railway (master)][railway_button]][railway_master] | [![Deploy on Railway (dev)][railway_button]][railway_dev] |

[railway_button]: https://railway.app/button.svg

[railway_master]: https://railway.app/new/template/UojxgA?referralCode=PEOFMi

[railway_dev]: https://railway.app/new/template/1_Wcri?referralCode=PEOFMi

After deployed, check the bot log to see if it is using PostgreSQL (`postgre`), otherwise, all the data will be lost when updating.

_Please note that if you deploy RSStT without using the above buttons, you must manually add the PostgreSQL plug-in._

### Update

Turn to the fork automatically created by Railway and switch to the branch you've deployed, then click `Fetch upstream` and `Fetch and merge`.

## Option 3: Heroku

> Heroku accounts with no verified payment method have only 550 hours of credit per month (about 23 days), and up to 1,000 hours per month with any verified payment methods.

### Deploy

|                            master                            |                          dev                           |
|:------------------------------------------------------------:|:------------------------------------------------------:|
| [![Deploy to Heroku (master)][heroku_button]][heroku_master] | [![Deploy to Heroku (dev)][heroku_button]][heroku_dev] |

[heroku_button]: https://www.herokucdn.com/deploy/button.svg

[heroku_master]: https://heroku.com/deploy?template=https%3A%2F%2Fgithub.com%2FRongronggg9%2FRSS-to-Telegram-Bot%2Ftree%2Fmaster

[heroku_dev]: https://heroku.com/deploy?template=https%3A%2F%2Fgithub.com%2FRongronggg9%2FRSS-to-Telegram-Bot%2Ftree%2Fdev

### Keep the dyno "awake"

> **IMPORTANT**  
> If you deploy RSStT as a **free dyno**, it will sleep if the dyno receives no web traffic in 30 minutes. Sending commands to the bot will NOT help.

Turn to [Kaffeine](https://kaffeine.herokuapp.com/), filling your Heroku app name, and click `Give my app a caffeine shot every 30 minutes ☕`. You do not need to check `I want a bedtime!` as long as your account has a verified payment method since Heroku has no longer enforced 6-hour-per-day sleeps since 2017. However, if your account has no verified payment method, you may still want to check `I want a bedtime!`. By checking it, your dyno will have a 6-hour sleep per day, which ensures that it will not exhaust your 550-hour credit.

### Update

1. [Fork RSStT](https://github.com/Rongronggg9/RSS-to-Telegram-Bot/fork) to your GitHub account.
2. Use the instant deploy buttons above to deploy RSStT to Heroku.
3. Switch the `Deployment method` to `GitHub` (`Deploy` tab -> `Deployment method`) and connect the app to your fork.
4. Enable `Automatic deploys` (`Deploy` tab -> `Automatic deploys` -> `Enable Automatic Deploys`).
5. Each time upstream updates, turn to your fork and switch to the branch you've deployed, then click `Fetch upstream` and `Fetch and merge`.

## Option 4: Install from PyPI / Dirty run from source

### System requirements

> RSStT is tested only under the recommended system requirements.

|                      | **Minimum**                   | **Recommended** |
|----------------------|-------------------------------|-----------------|
| **Operating system** | Linux, Windows, macOS         | Linux           |
| **Architecture**     | x86, amd64, arm64             | amd64           |
| **Python**           | 3.7 (x84, amd64), 3.8 (arm64) | 3.9, 3.10       |
| **Free memory**      | 128MB                         | \> 384MB        |

### Prerequisites

> These fonts are used for HTML table rendering (to enable it, set the environment variable `TABLE_TO_IMAGE` to `1`). You may use WenQuanYi Zen Hei, WenQuanYI Micro Hei, Noto Sans CJK, Microsoft YaHei, or SimHei.

#### Debian / Ubuntu

```sh
sudo apt install -y fonts-wqy-microhei
```

#### Other Linux distributions / Windows / macOS

You know what to do. However, I cannot guarantee that the fonts can be recognized properly by matplotlib.

### Option 4.1: Install from PyPI

[![PyPI](https://img.shields.io/pypi/v/rsstt?logo=pypi&logoColor=white)](https://pypi.org/project/rsstt/)
[![PyPI publish status](https://img.shields.io/github/workflow/status/Rongronggg9/RSS-to-Telegram-Bot/Publish%20to%20PyPI?label=publish&logo=pypi&logoColor=white)](https://github.com/Rongronggg9/RSS-to-Telegram-Bot/actions/workflows/publish-to-pypi.yml)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/rsstt?logo=pypi&logoColor=white)](https://pypi.org/project/rsstt/)
[![PyPI - Implementation](https://img.shields.io/pypi/implementation/rsstt?logo=python)](https://www.python.org)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/rsstt?logo=python)](https://www.python.org)

> Create a virtual environment (`venv`) and activate it first if needed.
> Default config folder is `~/.rsstt`.

```sh
pip3 install -U pip setuptools
pip3 install rsstt
mkdir -p ~/.rsstt
wget https://raw.githubusercontent.com/Rongronggg9/RSS-to-Telegram-Bot/dev/.env.sample -O ~/.rsstt/.env
vi ~/.rsstt/.env  # fill in env variables
python3 -m rsstt
```

### Option 4.2: Dirty run from source

[![GitHub repo size](https://img.shields.io/github/repo-size/Rongronggg9/RSS-to-Telegram-Bot?logo=github)](https://github.com/Rongronggg9/RSS-to-Telegram-Bot/archive/refs/heads/dev.zip)
[![GitHub release (latest SemVer including pre-releases)](https://img.shields.io/github/v/release/Rongronggg9/RSS-to-Telegram-Bot?include_prereleases&sort=semver&logo=github)](https://github.com/Rongronggg9/RSS-to-Telegram-Bot/releases)
[![GitHub last commit (dev)](https://img.shields.io/github/last-commit/Rongronggg9/RSS-to-Telegram-Bot/dev?logo=github)](https://github.com/Rongronggg9/RSS-to-Telegram-Bot/commits/dev)
[![GitHub commits since latest release (by SemVer including pre-releases)](https://img.shields.io/github/commits-since/Rongronggg9/RSS-to-Telegram-Bot/latest?include_prereleases&sort=semver&logo=github)](https://github.com/Rongronggg9/RSS-to-Telegram-Bot/commits/dev)

> Default config folder is `./config`, default `.env` path is `./.env` (placing it inside the config folder is also supported).

```sh
git clone https://github.com/Rongronggg9/RSS-to-Telegram-Bot.git
cd RSS-to-Telegram-Bot
pip3 install -r requirements.txt
cp .env.example .env
vi .env  # fill in env variables
python3 -u telegramRSSbot.py
```

###     * Advanced command line arguments

- `-h`, `--help`: show the help message and exit
- `-c`, `--config`: path to the config folder
