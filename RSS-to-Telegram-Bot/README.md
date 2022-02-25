# [RSS to Telegram Bot](https://t.me/RSStT_Bot)

**A Telegram RSS bot that cares about your reading experience**

[简体中文 README](README.zh.md)

[![Translating Status](https://hosted.weblate.org/widgets/rss-to-telegram-bot/-/svg-badge.svg)](https://hosted.weblate.org/engage/rss-to-telegram-bot/)
[![Build Status (master)](https://img.shields.io/github/workflow/status/Rongronggg9/RSS-to-Telegram-Bot/Publish%20Docker%20image/master?label=build%20%28master%29)](https://github.com/Rongronggg9/RSS-to-Telegram-Bot/actions/workflows/publish-docker-image.yml?query=branch%3Amaster)
[![Build Status (dev)](https://img.shields.io/github/workflow/status/Rongronggg9/RSS-to-Telegram-Bot/Publish%20Docker%20image/dev?label=build%20%28dev%29)](https://github.com/Rongronggg9/RSS-to-Telegram-Bot/actions/workflows/publish-docker-image.yml?query=branch%3Adev)
[![Docker Pulls](https://img.shields.io/docker/pulls/rongronggg9/rss-to-telegram)](https://hub.docker.com/r/rongronggg9/rss-to-telegram)
[![GitHub Stars](https://img.shields.io/github/stars/Rongronggg9/Rss-to-Telegram-Bot?style=social)](https://github.com/Rongronggg9/RSS-to-Telegram-Bot/stargazers)

<a href="https://t.me/RSStT_Bot"><img src="docs/resources/RSStT_icon.svg" width = "256" height = "256" alt="RSStT_icon"/><a/>

|   Public bot   |  Telegram channel  |  Discussion group  |
|:--------------:|:------------------:|:------------------:|
|  [@RSStT_Bot]  |  [@RSStT_Channel]  |   [@RSStT_Group]   |

| [CHANGELOG] | [Documentation] | [Channels Using RSStT] |
|:-----------:|:---------------:|:----------------------:|

[@RSStT_Bot]: https://t.me/RSStT_Bot

[@RSStT_Channel]: https://t.me/RSStT_Channel

[@RSStT_Group]: https://t.me/RSStT_Group

[CHANGELOG]: docs/CHANGELOG.md

[Documentation]: docs

[Channels Using RSStT]: docs/channels-using-rsstt.md

[![Deploy on Railway](https://railway.app/button.svg)](docs/deployment-guide.md#option-2-railwayapp)

**Important**: If you have your own RSStT bot (v1), please read the [migration guide](docs/migration-guide-v2.md) to learn how to migrate to v2.

## Highlights

- Multi-user
- I18n
    - English, Simplified Chinese, Cantonese, Italian, and [more](docs/translation-guide.md)!
- The content of the posts of an RSS feed will be sent to Telegram
    - Keep rich-text format
    - Keep media
    - Automatically determine whether the title of the RSS feed is auto-filled, if so, omit the title
    - Automatically show the author-name
    - Automatically replace emoji shortcodes with emoji
    - Automatically replace emoji images with emoji or its description text
    - Automatically split too-long messages
        - If configured Telegraph, the message will be sent via Telegraph
- Individual proxy settings for Telegram and RSS feeds
- OPML importing and exporting
- Subscription customization
- Optimized performance (see also the [FAQ](docs/FAQ.md#q-how-is-the-performance-of-the-bot-it-appears-to-have-a-slight-memory-leak-problem))
- User-friendly
- HTTP Caching

<img src="docs/resources/example1.png" width = "300" alt=""/><img src="docs/resources/example3.png" width = "300" alt=""/><img src="docs/resources/example4.png" width = "300" alt=""/>

## Deployment

Read the deployment guide [here](docs/deployment-guide.md).

## FAQ

Read the FAQ [here](docs/FAQ.md).

## Translation

Read the translation guide [here](docs/translation-guide.md).

You can help to translate the bot using [Hosted Weblate](https://hosted.weblate.org/projects/rss-to-telegram-bot/). Special thanks to their free hosting service for libre projects!

<a href="https://hosted.weblate.org/engage/rss-to-telegram-bot/"><img src="https://hosted.weblate.org/widgets/rss-to-telegram-bot/-/open-graph.png" width = "500" alt="" /></a>

## Using the public bot

The [public bot](https://t.me/RSStT_Bot) comes with absolutely no warranty. I will try my best to maintain it, but I cannot guarantee that it will always work perfectly. Meanwhile, you should "fair use" the bot, avoid subscribing to too many RSS feeds.  
If you use the [public bot](https://t.me/RSStT_Bot) in your Channel, consider mentioning the bot (or this project) in your channel description (or pinned message) to let more people know about it. That's not a compulsion.

## Known channels using RSStT

Want to preview what the messages sent by RSStT look like? Here is a [list of channels using RSStT](docs/channels-using-rsstt.md).

## License

This project is licensed under the [AGPLv3 license](LICENSE). Closed-source distribution or bot-hosting are strictly prohibited. If you modify the code and distribute or host it, make sure any users who can use your bot can get the source code (by editing the repo URL in [`src/i18n/__init__.py`](src/i18n/__init__.py)).
