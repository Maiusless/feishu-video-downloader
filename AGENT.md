---
name: feishu-video-download
description: 飞书云盘视频批量下载 - 通过 Playwright + Range 分段下载绕过 IP 绑定和 CORS 限制
github: https://github.com/Maiusless/feishu-video-downloader
---

# 飞书云盘视频批量下载 — Agent 操作手册

> 加载本 skill 后按 Step 1→2→3→4 顺序执行

## 触发条件

用户要求从飞书云盘下载视频，或提到"飞书"+"下载""视频"等关键词时加载。

## 前置要求

- 服务器已安装 Playwright：`pip install playwright && playwright install chromium`
- Hermes 已设 `browser.allow_unsafe_evaluate: true`

## Step 1：提取 file token

在 Browserbase 浏览器中打开飞书文件夹页面：

```markup
browser_navigate(url="https://{domain}.feishu.cn/drive/folder/{FOLDER_TOKEN}")
```

然后在控制台执行：

```javascript
(function(){
  var s = window.store || window.__store__;
  if(!s) return 'no store';
  var st = s.getState ? s.getState() : s.state;
  var obs = st.entities && st.entities.objs;
  if(!obs) return 'no objs';
  var result = [];
  Object.keys(obs).forEach(function(k){
    var obj = obs[k];
    var data = obj.toJS ? obj.toJS() : obj;
    if(data.name && data.name.endsWith('.mp4'))
      result.push({name: data.name, token: data.obj_token || k});
  });
  result.sort(function(a,b){ return a.name.localeCompare(b.name, undefined, {numeric: true}); });
  return JSON.stringify(result);
})()
```

得到类似 `[{"name":"1.mp4","token":"xxx"},...]` 的 JSON。

## Step 2：准备下载脚本

将上一步的 token 列表写入 `/tmp/feishu_files.json`，然后用 `write_file` 创建下载脚本。

完整脚本在 [`download.py`](download.py)。

## Step 3：运行下载

```bash
cd /tmp && python3 download.py feishu_files.json
```

文件多时建议后台跑：

```markup
terminal(command="cd /tmp && python3 download.py feishu_files.json",
         background=true, notify_on_complete=true)
```

## Step 4：监控进度

```markup
process(action="poll", session_id="proc_xxx")
```

每 2-3 分钟检查一次。35 个文件约 7-8 GB，总耗时 30-60 分钟。

## 流地址格式

```
https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/video/{TOKEN}/?quality=1080p&mount_point=explorer
```

`data_version` 参数可选，不需要。

## 常见问题

| 问题 | 原因 | 解决 |
|------|------|------|
| `browser_console` fetch 被拦截 | 安全策略 | `hermes config set browser.allow_unsafe_evaluate true` |
| 文件页显示登录 | 访客 session 过期 | 回到文件夹页面重建 session |
| content-range 缺失 | 飞书服务器不返回该头 | 改用 `HEAD` 请求获取 `content-length` |
| 下载超时 | 文件过大 | 脚本已自动 4MB 分段 |
| curl 返回 401 | session IP 绑定 | 必须在 Playwright 浏览器内 fetch |
