# Changelog

## Published to PyPI, HTML table converter, and more (v2.2.1)

### Additions

#### Highlights

- **Published to PyPI**: RSStT is now available on [PyPI](https://pypi.org/project/rsstt/). You may install it with `pip install rsstt`. For more details, refer to the [Deployment Guide](deployment-guide.md).
- **HTML table converter**: An HTML table converter has been implemented to convert HTML tables to images. It requires the environment variable `TABLE_TO_IMAGE` to be set to `1`, and CJK fonts to be installed. Please do note that the converter is not perfect, cannot handle rich-text formatting, may not work for all HTML tables, and can potentially lead to a higher performance cost and longer processing time.

### Other additions

- **New l10n**: The Indonesian (`id`, Bahasa Indonesia) translation has been added.
- **Add `.env.sample`**: A sample `.env` file has been added.

### Enhancements

- **Natural sorting**: Send posts from the oldest to the newest.
- **Timed GC**: Perform a GC (garbage collection) every 10 minutes to clean up the memory.
- **Update l10n**: The Turkish (`tr`, Türkçe) translation has been updated.
- **Security**: Execute `git` outside of the shell.
- **Minor enhancements**

### Bug fixes

- **Misfired monitor job**: Increased the `misfire_grace_time` to 10s to avoid monitor jobs being misfired because of high load.
- **Deps bump**: Fixed an upstream bug preventing users from resetting all subscriptions to the user's default settings on a PostgreSQL-based instance.
- **Minor bug fixes**

## Channel remote management, more formatting options, and more (v2.2.0)

### Additions

#### Highlights

- **Channel/group remote management**: Now you can manage the subscription of your channel/group in the private chat with the bot. Most commands are supported. Just send commands like `/sub @username https://exmaple.com` or `/sub -10010000000000 https://exmaple.com`. (`@username` is the channel/group's username, `@` is required; `-10010000000000` is the channel/group's ID, it must start with `-100`)
- **More custom formatting options**:
    - **Media**: You can make Telegram messages come with no media (just text) if you want (by default, they always come with media if any media is attached to the post). Also, you can make Telegram messages come with only media and metadata (no content) if you want, only when any media is attached to the post, otherwise, they will still come with the content.
    - **Link Preview**: Now you can force disable link preview for Telegram messages.
    - **Source**: More sourcing formats available. Read the detailed description in the [Formatting Settings Guidebook](formatting-settings.md).
- **Deployment to Heroku**: The bot can now be deployed to Heroku. Read the detailed description in the [Deployment Guide](deployment-guide.md).
- **User permission management**: The bot manager can now manage the permissions of the bot users by using the `/user_info` command. In this way, the bot manager can set who (user/channel/group) can use the bot, even if the multi-user mode is disabled.

#### Other additions

- **Single-column table support**: Formerly, all HTML tables were dropped from the output. Now those tables with only one column are rendered as multi-line text. Note that multi-column tables will still be dropped from the output.
- **Audio fallback for [lizhi.fm](https://www.lizhi.fm)**: Automatically fallback to the less-quality version of the audio if the higher-quality version exceeds the file size limit. Only for [lizhi.fm](https://www.lizhi.fm).

### Enhancements

- **Prettified Telegraph post**: The format of Telegraph posts is prettified. In addition, all images and videos are using the media relay server to avoid anti-hotlinking.
- **Non-HTTP hyperlinks**: Non-HTTP hyperlinks are not supported by Telegram. The bot will automatically convert them to bare URLs.
- **Enclosure cleaning**: If an enclosure with a non-HTTP URL is already included in a link in the post, it will be removed.
- **Lazy media validator**: The media validator is now lazy. It will only run if a post will be probably sent as Telegram messages. This will reduce CPU usage and network traffic.
- **Enhanced image dimension extraction**: Image dimension extraction is now faster and more flexible. If failed, the bot will try to extract the dimension using [images.weserv.nl](https://images.weserv.nl).
- **L10n update**: Turkish (Türkçe) l10n file updated. (English, Simplified Chinese / 简体中文, Traditional Chinese / 正體中文, Cantonese / 廣東話 are always up-to-date.)
- **Improved Docker build caching**: If the dependencies are not changed, no need to fetch the whole Docker image again. Just use the cached dependencies and fetch the latest source code.
- **Extract git info from Railway.app env variables**: Deployment on Railway.app can now recognize the git info.
- **Minor enhancements**

### Bug fixes

- **Python 3.7 compatibility**: The previous version of the bot broke the compatibility with Python 3.7. Now it has been fixed. Please note that only x86 and amd64 architectures are supported. For arm64, the minimum Python version requirement is 3.8.
- **EntitiesTooLongError**: Posts with tons of text hyperlinks could cause Telegram API to throw this error. Now the bot will try to fix this error by more aggressive post splitting.
- `<div>`: The bot will now ensure that each `<div>` tag takes up a whole line.
- **Unnecessary image fallback**: The bot will no longer fall back all images to file if at least one image needs to be sent as a file.
- **Web retry**: Added a need-to-retry exception.
- **Webpage decode error**: `cchardet` is not robust enough to handle all feeds. Now the bot will try to detect the encoding of the webpage according to the XML encoding declaration. Also, if `cchardet` returns a not-supported encoding, the bot will try to decode the webpage using UTF-8. Any character that cannot be decoded will be replaced with `�`.
- **Extracting image dimension from Exif thumbnail**: Some images may contain a thumbnail in the Exif data. The bot will now avoid extracting the dimension from the thumbnail.
- **Minor bug fixes**

## Custom format, new l10n, improved media fallback, and more (v2.1.0)

Official public bot [@RSStT_Bot](https://t.me/RSStT_Bot) is always using the `dev` branch. If you are using it, you may have noticed the new features. Since new commands are added, please use `/lang` command once again and select your language to let the bot update your command list.

### BREAKING CHANGES

- Inline mode is now required to be enabled due to new custom settings. Go to [@BotFather](https://t.me/BotFather), send `/setinline`, select your bot, and reply with an inline placeholder you like. For example, [@RSStT_Bot](https://t.me/RSStT_Bot) is using `Please input a command to continue...`.

### Additions

#### Highlights

- **More custom formatting options**: `/set` command now gains its full power. You can control media or any metadata to be displayed or not. Adding your custom hashtags and setting your custom subscription title are all possible, but the inline mode is required to be enabled. Read the detailed description of formatting settings in the [Formatting Settings Guidebook](formatting-settings.md).
- **User's default formatting settings**: Use `/set_default` to set your default formatting settings. It applies to all your new subscriptions and if you like, you can make existing subscriptions use them. It is useful if you want to set similar settings for most of your subscriptions.

![img.png](resources/formatting.png)

- **New l10n**: Italian (Italiano), Turkish (Türkçe), Catalan (Català), and French (français). Feel like adding your language? Please read the translation guide [here](translation-guide.md).
- **Feed sniffer**: If you try to subscribe to a webpage instead of a feed, the bot will try to sniff the feed from the webpage. (Note: this only works if the webpage contains a feed link.)
- **Enclosure support**: The bot can now extract enclosures from posts. Enjoy listening to podcasts or downloading attachments!
- **`<audio>` support**: The bot can now extract audio from post content. Enjoy listening to podcasts!
- **Send long images as files**: The bot can now send long images as files. This can prevent Telegram from compressing the image and making it unreadable.
- **OPML importing w/ custom title**: You can now import subscriptions from OPML files, without losing your custom title. The bot will ask you if the bot should use the custom titles from the OPML file or not.
- **OPML exporting w/ custom title**: You can now export your subscriptions to an OPML, without losing your custom title.

#### Other additions

- **Image validation for more formats**: The bot can now judge the validity of non-JPEG images and fall back automatically to alternative images (if any) when the image is invalid.
- **Image fallback (`srcset`)**: The bot can now fall back an image to its alternative images (`<img srcset="...">`, if any) when the image is invalid.
- **Image fallback for pixiv**: The bot can now fall back an image from pixiv to its other sizes when the image is invalid. (#41)
- **Image fallback for all images**: The bot can now use images.weserv.nl to fall back an invalid image to an image valid for Telegram API.
- **Video fallback**: The bot can now fall back a video to its alternative videos (`<video><source>...</video>`, if any) or its poster (`<video poster="...">`, if any) when the video is invalid.
- **WEBP and SVG support**: The bot can now use images.weserv.nl to convert WEBP and SVG to PNG, to make them compatible with Telegram API.
- **Media uploader**: The bot now uploads media by using bare MTProto API calls, instead of using the effective method of telethon. This is to avoid unnecessary media fallback and to improve performance.

### Enhancements

- **Page number**: When a command needs to be paginated, the bot will show the current page number.
- **`/unsub_all` confirmation and backup**: When you unsubscribe from all feeds, the bot will ask you to confirm and send you a backup.
- **Cancel**: Some commands can be canceled by tapping on the `Cancel` button.
- **Custom monitor interval**: You have now more choice of monitor interval, and if you want, you can set any interval you like (need the inline mode to be enabled, note that the bot manager can prevent ordinary users from setting a too-small value).
- **Deactivating reason**: When a subscription is deactivated due to too many errors, the bot will tell you the reason.
- **Drop more icons**: Some posts have annoying icons. The bot can now detect and drop more.
- **Monitor tasks order randomization**: The order of the monitor tasks is randomized.
- **Retry when Telegram internal error occurs**: When Telegram internal error occurs, the bot will retry to send the message.
- **Rewritten post parser**: The post parser is rewritten to be more flexible and gain the ability to support custom formatting.
- **Rewritten rich-text splitter**: The rich-text splitter is rewritten to be more stable, flexible and gain the ability to support custom formatting. This also prevents it from prematurely splitting the text.
- **Command speedup**: Some commands are now faster.
- **`/test` formatting**: The `/test` command now uses the user's default formatting settings or the formatting settings of the feed (if subscribed). (Note: only the bot manager can use this command.)
- **Minor enhancements**

### Bug fixes

- **Feed title not updated**: When a feed updates its title, the bot will now update the title in the DB and send messages with the new title.
- **Content too long**: Those commands that may contain long content now will be either shortened or paginated. If still too long, the bot will prompt you.
- **Too many entities**: The bot now ensures that the number of formatting entities in a message is not greater than 100 (Telegram API limit), otherwise a split is made. This is to prevent messages from losing their formatting.
- **Potential deadlock**: A potential deadlock issue has been fixed.
- **Improper white-space and linebreak policy**: The bot can now avoid unintended white spaces and linebreaks in messages, especially for weird feeds. This also applies to the feed/post title and post author.
- **Minor bug fixes**

## Multi-user, i18n, improved user-friendliness, and more (v2.0.0)

Official public bot: [@RSStT_Bot](https://t.me/RSStT_Bot)

**This is a major release. It introduces some major breaking changes. You must migrate to the new version manually.**  
**PLEASE READ THE [MIGRATION GUIDE](migration-guide-v2.md) BEFORE UPDATING!**

### BREAKING CHANGES

- User and subscription management has been rewritten. The bot now can be used by multiple users and each subscription may have its individual monitoring interval. Thus, env variables `CHATID` and `DELAY` are deprecated and of no use.
    - The default behavior is to run as a multi-user bot. If you still would like to limit the bot to serve you only, follow the [migration guide](migration-guide-v2.md).
- Redis support has been dropped. Only SQLite and PostgreSQL are supported.

### Additions

#### Highlights

- **Multi-user**: The bot can be used by any users, or in channels and groups (unless env variable `MULTIUSER` is set to `0`).
- **I18n**: The bot now supports multiple languages. Currently, <ins>English (en)</ins>, <ins>Simplified Chinese (简体中文, zh-Hans)</ins> and <ins>Cantonese (廣東話, yue)</ins> are supported. You can contribute by translating the bot to your language following the [translation guide](translation-guide.md).
- **User-friendly**: You can use most commands interactively, no need to remember their syntax.
- **HTTP Caching**: The bot has implemented the necessary parts of [RFC7234](https://datatracker.ietf.org/doc/html/rfc7234) to "cache" feeds. It can reduce the servers loads of both the bot and the feed provider.

#### Other additions

- **Customizing subscriptions**: Subscriptions can be customized. Currently, only the settings below can be customized. Other settings are WIP.
    - **Pausing**: You can deactivate a subscription. In this way, you can make the bot pause to send updates of it.
    - **Muting**: You can mute a subscription. In this way, when the bot sends updates of it, silent messages will be sent. (You will still receive notifications, but no sound.)
    - **Interval**: You can change the monitoring interval of a subscription.
- **Documentation**: The bot now has documentation. You can find it at [docs]().

### Enhancements

- **Better feed history management**: All posts in a feed are now hashed and stored. This allows you to subscribe to almost any feeds without missing posts.
- **Better error handling**: The bot now has better error handling. It will now try to recover from errors and retry.
- **Better logging**: The bot now has better logging.
- **Better performance**: The bot now has a better performance.
- **Dependence bump**: Dependencies have been bumped to the latest version. Potential security vulnerabilities have been fixed.
- **Proxy bypassing**: If env variable `PROXY_BYPASS_PRIVATE` is set, the bot will bypass proxy for private IPs. And will bypass proxy for domains listed in env variable `PROXY_BYPASS_DOMAINS`.
- **Bugfixes**: A few bugfixes.

## Rushed release to fix login (v1.6.1)

**This is a rushed release. It bumps the dependency `telethon` to the latest version. Please upgrade to this version immediately to avoid being unable to login due to the outdated dependency.**

The bot is currently being actively developed on the `multiuser` branch but has not been merged back yet to avoid introducing breaking changes too early. If you would like to try the multi-user version, there is a public demo [@RSStT_Bot](https://t.me/RSStT_Bot).

### Additions

- `.env` file support (only for manual execution, not for docker)
- Unescape HTML-escaped post title
- Use the title as the content of a post if the latter is of no text

### Enhancements

- Minor bug fixes
- Introduce some workarounds to avoid being flood-controlled frequently
- Introduce some deps to speed up HTTP requests

## Switching to MTProto, OPML support, and more (v1.6.0)

### BREAKING CHANGES

- The telegram bot library has been migrated from `python-telegram-bot` (which uses HTTP Bot API and is synchronous) to `telethon` (which uses MTProto Bot API and is asynchronous)
    - However, to use MTProto Bot API, an API key is needed. The bot has 7 built-in API keys (collected from the Internet) and in most cases, it should not be unable to log in. But if so, please obtain your own API key
      (see [docker-compose.yml.sample](https://github.com/Rongronggg9/RSS-to-Telegram-Bot/blob/53f11a4739/docker-compose.yml.sample#L43) for details)

### Additions

- Thanks to the migration of the Telegram bot library, the bot can now connect to its DC directly, need not detour through the HTTP Bot API, and keep polling to get new messages. Which makes the bot receive and reply to messages more rapidly and lightweight. Even if the HTTP Bot API is down, the bot can still run unaffectedly.
  (more details: [Advantages of MTProto over Bot API](https://docs.telethon.dev/en/latest/concepts/botapi-vs-mtproto.html#advantages-of-mtproto-over-bot-api), [MTProto vs HTTP Bot API](https://github.com/LonamiWebs/Telethon/wiki/MTProto-vs-HTTP-Bot-API))
- Support parsing more HTML elements
    - `<iframe>`
    - `<video><source><source>...</video>`
    - `<code>`
    - `<pre>`
- Support OPML importing and exporting
- Support sending too-long post via Telegraph (env variable `TELEGRAPH_TOKEN` must be set)
- Support using Redis as DB
    - Note: This is a workaround for deploying the bot on [railway.app](), will be dropped in the future
- Support arm64 (docker build)
- Support resending a message using a media relay server if Telegram cannot send a message with media due to Telegram server instability or network instability between the media server and Telegram server
- Support colored logging
- `docker-compose.yml.sample`
- `/version` command to check bot version
- Automatically use proxy if global proxy (env variable `SOCKS_PROXY`/`HTTP_PROXY`) set

### Enhancements

- Assign feed monitoring tasks to every minute, instead of executing all at once each `DELAY`
    - Thus, env variable `DELAY` can only be 60~3600
    - Note: env variable `DELAY` will be deprecated in the future
- Recognize a post by its `guid`/`id` instead of `link`
- Simplify the output of `/list`
- Bump Python to 3.9 (docker build)
- Minor fixes

## Complete rewrite of the post parser (v1.5.0)

- The Post parser is completely rewritten, more stable, and can keep text formatting as much as possible
- GIF Support
- When the message is more than 10 pieces of media, send it in pieces
- Support video and pictures to be mixed in the same message arbitrarily
- Invalid media are no longer directly discarded, but attached to the end of the message as a link
- Automatically determine whether the title of the RSS feed is auto-filled, if so, omit the title
- Automatically show the author-name
- Automatically replace emoji shortcodes with emoji
- Automatically replace emoji images with emoji or its description text
- When an image cannot be sent due to the instability of telegram API, the image server will be automatically replaced and resent
    - Only for Weibo images, non-Weibo images will be attached to the end of the message as a link
- Improve the text length counting method, no longer cause the message to be divided wrongly due to a long link URL
- Change the user-agent, because some websites have banned the UA of Requests
- Logging improvement

## Initial release (v1.0.0)

initial public release
