# 飞书云盘视频批量下载器 🎬

> Feishu / Lark cloud drive video batch downloader

通过 **Playwright + Range 分段下载** 绕过飞书的 IP 绑定和 CORS 限制，从**访客/外部链接**权限的文件夹中批量下载 MP4 视频。

## ✨ 特点

- ✅ 无需真实账号登录 — 访客身份即可下载
- ✅ 绕过 IP 绑定 — 在 Playwright 浏览器内完成请求
- ✅ 绕过 CORS — 通过 `page.evaluate()` 执行 fetch
- ✅ 大文件分段 — 4MB 一块，稳定不超时
- ✅ 批量下载 — 一次性下完整个文件夹

## 📋 适用场景

- 飞书外部共享文件夹，视频可播放但**无法直接下载**
- 访客/外部协作身份，无下载权限
- 服务器端 curl 请求返回 401（IP 绑定）
- 浏览器控制台 API 调用被 CORS 拦截

## 🚀 快速开始

### 前置条件

```bash
pip install playwright
playwright install chromium
```

### 第一步：获取文件 token

在飞书文件夹页面打开浏览器控制台 (F12)，粘贴：

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
    if(data.name && data.name.endsWith('.mp4')){
      result.push({name: data.name, token: data.obj_token || k});
    }
  });
  result.sort(function(a,b){
    return a.name.localeCompare(b.name, undefined, {numeric: true});
  });
  console.log(JSON.stringify(result, null, 2));
  window._feishuFiles = result;
})();
```

把输出的 JSON 保存为 `files.json`。

### 第二步：批量下载

```bash
python3 download.py files.json
```

## ⚙️ 工作原理

```
浏览器 React Store → 提取 file token
         ↓
Playwright 无头浏览器（带访客 session）
         ↓
HEAD 请求获取文件大小
         ↓
Range 分段 fetch（4MB/块）
         ↓
ArrayBuffer → base64 → Python 解码
         ↓
写入 /data/ 目录
```

### 流地址格式

```
https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/video/{TOKEN}/?quality=1080p&mount_point=explorer
```

## 📦 项目结构

```
feishu-video-downloader/
├── README.md           # 本文件
├── download.py         # 批量下载脚本
├── get_tokens.js       # 获取 token 的 JS 代码
└── files.json          # 文件列表（从控制台导出）
```

## ⚠️ 注意事项

| 问题 | 解决 |
|------|------|
| `browser_console` fetch 被拦截 | 设置 `browser.allow_unsafe_evaluate: true` |
| 文件过大（200MB+）超时 | 脚本已自动 4MB 分段 |
| 访客 session 过期 | 先访问文件夹页面建立 session |
| 文件名含特殊字符 | 自动替换 `/` 等字符 |

## 📜 License

MIT
