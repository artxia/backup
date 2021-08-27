# PT-Gen on Cloudflare Worker
[![FOSSA Status](https://app.fossa.io/api/projects/git%2Bgithub.com%2FRhilip%2Fpt-gen-cfworker.svg?type=shield)](https://app.fossa.io/projects/git%2Bgithub.com%2FRhilip%2Fpt-gen-cfworker?ref=badge_shield)
[![Build Status](https://travis-ci.com/Rhilip/pt-gen-cfworker.svg?branch=master)](https://travis-ci.com/Rhilip/pt-gen-cfworker)

基于 [BFDZ/Pt-Gen v0.4.7](https://github.com/BFDZ/PT-Gen/commit/950b85de16d9532e847a0756f165d1b29f09dd31) 改写，
使之可以直接在Cloudflare Worker上使用。

如果你没有构造环境，请直接复制使用 [build分支](https://github.com/Rhilip/pt-gen-cfworker/tree/build) 下的
[script.js](https://github.com/Rhilip/pt-gen-cfworker/blob/build/script.js) 文件。

否则请参照 `.Travis.yml` 文件构造方法，直接使用`wrangler`搭建Cloudflare-Worker。

## 本项目请求方法

API Point：
 - https://ptgen.rhilip.info/
 - **！！！大批量请求时，请勿使用测试DEMO站点，请自己搭建cf-worker！！！**

`资源搜索` 请求字段：
  - search: 搜索字符串
  - source: 见下表 `资源来源站点`，不填时默认为 `douban`

`简介生成` 请求字段（方法1，推荐）：
  - url：见下表 `链接格式（Regexp）`

`简介生成` 请求字段（方法2）：
  - site: 见下表 `资源来源站点`
  - sid: 资源在对应站点的唯一id

## 支持资源链接

| 资源来源站点 | 搜索支持 | 链接格式（Regexp） |
| :---: | :---: | :------|
| douban | √ | `/(?:https?:\/\/)?(?:(?:movie\|www)\.)?douban\.com\/(?:subject\|movie)\/(\d+)\/?/` |
| imdb | √ | `/(?:https?:\/\/)?(?:www\.)?imdb\.com\/title\/(tt\d+)\/?/` |
| bangumi | √ | `/(?:https?:\/\/)?(?:bgm\.tv\|bangumi\.tv\|chii\.in)\/subject\/(\d+)\/?/` |
| steam | × | `/(?:https?:\/\/)?(?:store\.)?steam(?:powered\|community)\.com\/app\/(\d+)\/?/` |
| indienova | × | `/(?:https?:\/\/)?indienova\.com\/game\/(\S+)/` | 
| epic | × | `/(?:https?:\/\/)?www\.epicgames\.com\/store\/[a-zA-Z-]+\/product\/(\S+)\/\S?/` |

> update 2020.11.23 : 由于 steam 服务器对于 cf-worker 访问进行限制 （ 见[#10](https://github.com/Rhilip/pt-gen-cfworker/issues/10) ）， 目前服务的 steam 相关资源生成均无法使用。

## 环境变量及 KV 命名空间

通过设置环境变量可以使得 pt-gen-cfworker 能够实现一些额外的功能，当前有以下 环境变量：

| 变量 | 说明 |
|:---:|:---|
| `AUTHOR` | 用于重写api返回的作者信息 |
| `APIKEY` | 只允许带有 `&apikey={APIKEY}` 的请求访问资源 |
| `PT_GEN_STORE` | *KV Storage*，请在 `KV 命名空间绑定` 面板而不是环境变量面板设置！！！ |
| `DOUBAN_COOKIE` | 豆瓣Cookie，使得能访问部分登录可见的资源 |
| `INDIENOVA_COOKIE` | indienova 的 Cookie，见 [#15](https://github.com/Rhilip/pt-gen-cfworker/issues/15) |

## License
[![FOSSA Status](https://app.fossa.io/api/projects/git%2Bgithub.com%2FRhilip%2Fpt-gen-cfworker.svg?type=large)](https://app.fossa.io/projects/git%2Bgithub.com%2FRhilip%2Fpt-gen-cfworker?ref=badge_large)
