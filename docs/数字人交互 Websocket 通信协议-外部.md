**数字人交互 Websocket 通信协议-外部**

**Websocket URL**

wss://openspeech.bytedance.com/virtual\_human/avatar\_live/live

**交互阶段与协议帧**

**开播或重连**

**Client-Side**

**开播或重连初始化信息**

Message Type：Text

Header: |CTL|00|

Body:

| 参数名称 | 参数类型 | 参数层级 | 是否必需 | 参数含义 | 备注 |
| :---- | :---- | :---- | :---- | :---- | :---- |
| live | object | 1 | 必需 | 直播会话相关配置 |  |
| live\_id | string  | 2 | 必需  | 直播 ID | 需要保证唯一，建议采用: {公司名\_直播名} 一个 live\_id 只能开播一次，不能重复使用 |
| auth | object | 1 | 必需 | 鉴权相关配置 |  |
| appid | string | 2 | 必需 | 数字人账号 ID |  |
| token | string | 2 | 必需 | 数字人账号 Token |  |
| avatar | object | 1 | 必需 | 数字人相关信息 |  |
| avatar\_type | string | 2 | 必需 | 数字人类型 | pic：单图数字人 3min：3min 克隆数字人 |
| input\_mode | string | 2 | 必需 | 驱动模式 | audio：音频驱动 |
| role | string | 2 | 必需 | 形象名称 | 形象唯一 id，对应训练获得的 resource\_id |
| background | string | 2 | 非必需 | 背景 URL | 需要带有图片格式后缀，如 .png .jpg |
| video | object | 2 | 非必需 | 视频画面尺寸信息 |  |
| video\_width | int | 3 | 非必需 | 视频宽 | 取值范围 \[240, 1920\] |
| video\_height | int | 3 | 非必需 | 视频高 | 取值范围 \[240, 1920\] |
| bitrate | int | 3 | 非必需 | 数字人码率 | 单位为 kbps，取值范围 \[100, 8000\]，默认 2000 |
| role\_conf | object | 2 | 非必需 | 形象配置 |  |
| role\_width | int | 3 | 非必需 | 形象大小 | 100\<=值\<=1920\*3，有默认值，主播高度会自动推导，role\_width 过大，主播下半身可能会超出屏幕 |
| role\_left\_offset | int | 3 | 非必需 | 形象左边距 | 默认人物正中，值小于 0 或 role\_left\_offset \+ role\_width \> video\_width时，主播会左右超出屏幕 |
| role\_top\_offset | int | 3 | 非必需 | 形象上边距 | 0 \<= role\_top\_offset \< video\_height |
| streaming | object | 1 | 必需 | 推流相关配置 |  |
| type  | string | 2 | 必需  | 推流方式 | rtmp：RTMP bytertc：ByteRTC |
| rtmp\_addr  | string | 2 | 当 type=rtmp 时必需 | RTMP 推流地址 | 因目前服务都部署在国内机房，对于无法调通的国外推流地址，及有合流转推需求的客户，请使用[RTC 转推直播能力](https://www.volcengine.com/docs/6348/69833) |
| rtc\_app\_id | string | 2 | 当 type=bytertc 时必需 | ByteRTC 账号 ID |  |
| rtc\_room\_id | string | 2 | 当 type=bytertc 时必需 | ByteRTC 房间 ID |  |
| rtc\_uid  | string | 2 | 当 type=bytertc 时必需 | ByteRTC 推流用户 ID |  |
| rtc\_token | string | 2 | 当 type=bytertc 时必需 | ByteRTC 推流临时 token |  |

请求示例：

| JSON{    "live": {        "live\_id": "company\_livename"    },    "auth": {        "appid": "avatar\_appid",        "token": "access\_token"    },    "avatar": {        "avatar\_type": "3min",        "input\_mode": "audio",        "role": "xxx",        ... // 其他 avatar 字段    },    "streaming": {        "type": "bytertc",        "rtc\_app\_id": "xxx",        "rtc\_room\_id": "xxx",        "rtc\_uid": "xxx",        "rtc\_token": "xxx",    }} |
| :---- |

**Server-Side**

**确认建立连接**

Message Type：Text

Header: |MSG|00|

Body:

| 参数名称 | 参数类型 | 参数层级 | 是否必需 | 参数含义 | 备注 |
| :---- | :---- | :---- | :---- | :---- | :---- |
| code | int | 1 | 必需 | 状态码 | 1000：成功 其它：错误 详见下述[服务相关状态码](https://bytedance.larkoffice.com/wiki/UKf8wkcvXir5Epk4mPQcxsdwnad#share-YBXcdQLTFoft1XxdJyscd1ltn5c) |
| message | string | 1 | 必需 | 状态信息 | code=1000 时为 success 其它时为错误信息 |

**播放状态反馈**

**Server-Side**

**返回合成状态**

Message Type：Text

Header: |DAT|02|

Body:

| 参数名称 | 参数类型 | 参数层级 | 是否必需 | 参数含义 | 备注 |
| :---- | :---- | :---- | :---- | :---- | :---- |
| type | string | 1 | 必需 | 事件类型 | Avatar 内部事件，常用值： voice\_start：播报开始 voice\_continue：播报中 voice\_end：播报停止 |
| data | object | 1 | 非必需 | 事件数据 |  |
| extra\_data | string | 2 | 当对应帧有 extra\_data 时必需 | 自定义数据 | 若驱动音频带有 extra\_data，会在合成并推流到对应帧时将 extra\_data 放入某个事件内返回 |

**实时驱动**

**Client-Side**

**音频驱动**

Message Type：Text

Header: |DAT|01|

Body: SSML

| Plain TextSSML 示例\<speak\>\<audio url="http://xxx/xxx.wav" format="wav"/\>\</speak\> |
| :---- |

音频长度上限 10min，format 支持 pcm|wav|mp3

**流式音频驱动**

Message Type：Binary

Header: |DAT|02|

Body: 二进制音频数据（PCM）

16kHz 单通道 2字节深度，长度不小于 40ms（1280 字节，一帧视频帧对应的音频长度）

**结构化流式音频驱动（暂未开放）**

Message Type：Text

Header: |DAT|04|

Body:

| 参数名称 | 参数类型 | 参数层级 | 是否必需 | 参数含义 | 备注 |
| :---- | :---- | :---- | :---- | :---- | :---- |
| audio  | string | 1 | 必需 | 音频 | base64 编码的音频数据 音频应为 16kHz、单通道、2字节深度的 PCM，长度不小于 40ms（1280 字节，一帧视频帧对应的音频长度） |
| extra\_data | string | 1  | 非必需 | 自定义数据 | extra\_data 长度上限为 4kB 合成时会将 extra\_data 附在当前音频包对应的首帧，并以合成状态事件返回，见**播放状态反馈-返回合成状态-Body-data-extra\_data**；当使用 ByteRTC 推流时，extra\_data 会作为对应视频帧的 SEI 一起推出 |

注：extra\_data 当前仅在 3min 数字人生效

**流式音频驱动结束命令**

Message Type：Text

Header: |CTL|12|

**强制打断**

**Client-Side**

| 目前仅支持在实时驱动（无剧本）模式下进行强制打断 |
| :---- |

**立即打断当前播报并进入静默状态**

Message Type：Text

Header: |CTL|03|

**关播**

**Client-Side**

**正常结束直播**

Message Type：Text

Header: |CTL|01|

服务收到结束直播消息后会以 1000 作为 code 关闭 websocket 连接

**异常通知**

**Server-Side**

**服务异常通知**

Message Type：Text

Header: |MSG|01|

Body:

| 参数名称 | 参数类型 | 参数层级 | 是否必需 | 参数含义 | 备注 |
| :---- | :---- | :---- | :---- | :---- | :---- |
| code | int | 1 | 必需 | 错误码 | 详见下述[服务相关状态码](https://bytedance.larkoffice.com/wiki/UKf8wkcvXir5Epk4mPQcxsdwnad#share-YBXcdQLTFoft1XxdJyscd1ltn5c) |
| message | string | 1 | 必需 | 错误信息 |  |

服务发送异常通知后会以 4999 作为 code 关闭 websocket 连接

**心跳**

**Server-Side**

**服务端维持心跳**

通过 websocket 自带的 Ping/Pong 机制实现心跳，服务端每5s发送一次 Ping 包，客户端收到 Ping 包后应立即返回 Pong 包进行确认。服务端和客户端应自行对心跳消息进行超时处理（如3倍的心跳间隔）

鉴于前端无法收发 websocket 自带的 Ping/Pong 消息，服务端会同时每5s发一包以下格式的消息：

Message Type：Text

Header: |MSG|02|

**协议帧汇总**

**Client-Side**

| Header | Body | Message Type | 用途 |
| :---- | :---- | :---- | :---- |
| |CTL|00| | JSON | Text | 开播或重连初始化信息 |
| |CTL|01| | N/A | Text | 正常结束直播 |
| |CTL|03| | N/A | Text | 强制打断 |
| |CTL|12| | N/A | Text | 流式音频驱动结束命令 |
| |DAT|01| | SSML | Text | 音频驱动 |
| |DAT|02| | Binary PCM Data | Binary | 流式音频驱动 |
| |DAT|04| | JSON | Text | 结构化流式音频驱动 |

**Server-Side**

| Header | Body | Message Type | 用途 |
| :---- | :---- | :---- | :---- |
| |MSG|00| | JSON | Text | 确认建立连接，状态码详见下述[服务相关状态码](https://bytedance.larkoffice.com/wiki/UKf8wkcvXir5Epk4mPQcxsdwnad#share-YBXcdQLTFoft1XxdJyscd1ltn5c) |
| |MSG|01| | JSON | Text | 服务异常通知，状态码详见下述[服务相关状态码](https://bytedance.larkoffice.com/wiki/UKf8wkcvXir5Epk4mPQcxsdwnad#share-YBXcdQLTFoft1XxdJyscd1ltn5c) |
| |MSG|02| | N/A | Text | 心跳 |
| |DAT|02| | JSON | Text | 返回合成状态 |

**服务相关状态码**

| 错误方 | Code | 含义 | 举例 |
| :---- | :---- | :---- | :---- |
|  | 1000 | 成功 | 初始化信息填写合理，正常开播 |
| **Client** | 4000 | 请求错误 | 请求解析失败 未填写必填字段 |
|  | 4001 | 鉴权错误 | 鉴权未通过 |
|  | 4002 | 并发超限 | 请求并发超出了事先申请的并发额度 |
|  | 4003 | 连接过多 | 同时有超过一个连接控制同一直播 |
|  | 4004 | Live ID 重复 | 请求开播的 Live ID 已在使用中 |
|  | 4005 | RTMP 推流地址重复 | 请求开播的 RTMP 推流地址已在使用中 |
|  | 4006 | 直播不存在 | 进行其它操作时直播不在开播中 |
|  | 4007 | 打断无效 | 在非实时驱动模式下进行打断 |
| **Server** | 5000  | Live 服务内部错误  | 直播初始化报错 连接上游服务失败 |
|  | 5001 | Avatar 服务内部错误 | 数字人服务初始化失败 |
|  | 5002 | 服务器忙 | 没有可用实例 |

