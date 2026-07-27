#!/usr/bin/env python3
"""
飞书云盘视频批量下载器
Feishu/Lark cloud drive video batch downloader

用法: python3 download.py files.json
"""

import asyncio
import base64
import json
import os
import sys
from playwright.async_api import async_playwright

CHUNK_SIZE = 4 * 1024 * 1024  # 4MB per chunk

def load_files(path):
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    # 支持两种格式: [{name, token}] 或 {name: token}
    if isinstance(data, dict):
        return [(v, k) for k, v in data.items()]
    return [(item['name'], item['token']) for item in data]

async def get_file_size(page, url):
    """通过 HEAD 请求获取文件大小"""
    info = await page.evaluate('''(url) => {
        return fetch(url, {method:'HEAD', credentials:'include'})
            .then(r => parseInt(r.headers.get('content-length') || '0'))
            .catch(e => 0)
    }''', url)
    return info

async def download_chunk(page, url, start, end):
    """下载指定 Range 的数据块，返回 bytes"""
    result = await page.evaluate('''(args) => {
        return fetch(args.url, {
            headers: {'Range': 'bytes=' + args.start + '-' + args.end},
            credentials: 'include'
        }).then(r => {
            if (!r.ok && r.status !== 206) throw new Error('HTTP ' + r.status);
            return r.arrayBuffer();
        }).then(buf => {
            var u = new Uint8Array(buf);
            var s = '';
            for (var i = 0; i < u.length; i++) s += String.fromCharCode(u[i]);
            return btoa(s);
        }).catch(e => 'ERR:' + e.message)
    }''', {'url': url, 'start': str(start), 'end': str(end)})
    
    if result.startswith('ERR:'):
        raise RuntimeError(f"Chunk download failed: {result}")
    return base64.b64decode(result)

async def download_file(page, name, token, output_dir):
    """下载单个视频文件"""
    safe_name = name.replace('/', '_').replace('\\', '_')
    path = os.path.join(output_dir, safe_name)
    
    if os.path.exists(path) and os.path.getsize(path) > 1024 * 1024:
        print(f"  ⏭ 已存在 ({os.path.getsize(path)/1024/1024:.1f}MB)")
        return True
    
    url = f"https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/video/{token}/?quality=1080p&mount_point=explorer"
    
    total = await get_file_size(page, url)
    if not total:
        print(f"  ❌ 无法获取文件大小")
        return False
    
    nchunks = (total + CHUNK_SIZE - 1) // CHUNK_SIZE
    print(f"  {total/1024/1024:.1f}MB, {nchunks} chunks", end='', flush=True)
    
    with open(path, 'wb') as f:
        for ci in range(nchunks):
            start = ci * CHUNK_SIZE
            end = min(start + CHUNK_SIZE - 1, total - 1)
            
            data = await download_chunk(page, url, start, end)
            f.write(data)
            
            if (ci + 1) % 25 == 0 or ci == nchunks - 1:
                pct = (ci + 1) / nchunks * 100
                print(f" {pct:.0f}%", end='', flush=True)
    
    actual = os.path.getsize(path)
    print(f" ✅ ({actual/1024/1024:.1f}MB)")
    return True

async def main():
    if len(sys.argv) < 2:
        print("用法: python3 download.py files.json")
        print("       python3 download.py files.json --dir /path/to/save")
        sys.exit(1)
    
    files = load_files(sys.argv[1])
    output_dir = sys.argv[3] if len(sys.argv) > 3 and sys.argv[2] == '--dir' else os.getcwd()
    folder_url = sys.argv[4] if len(sys.argv) > 4 else None
    
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"📦 共 {len(files)} 个文件")
    print(f"📂 保存到 {output_dir}")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=['--no-sandbox'])
        page = await browser.new_page()
        
        # 建立 session
        if folder_url:
            print("🔗 访问飞书文件夹建立 session...")
            await page.goto(folder_url, wait_until='networkidle', timeout=30000)
            await page.wait_for_timeout(2000)
        else:
            # 用第一个文件的页面建立 session
            first_token = files[0][1]
            print("🔗 访问飞书文件页面建立 session...")
            await page.goto(
                f"https://xcnqspqi998l.feishu.cn/file/{first_token}",
                wait_until='networkidle', timeout=30000
            )
            await page.wait_for_timeout(3000)
        
        ok = 0
        for i, (name, token) in enumerate(files):
            status = "⏭" if (os.path.exists(os.path.join(output_dir, name.replace('/', '_'))) 
                       and os.path.getsize(os.path.join(output_dir, name.replace('/', '_'))) > 1024*1024) else "..."
            print(f"[{i+1}/{len(files)}] {name} {status}", end='', flush=True)
            
            safe_name = name.replace('/', '_').replace('\\', '_')
            path = os.path.join(output_dir, safe_name)
            if os.path.exists(path) and os.path.getsize(path) > 1024 * 1024:
                ok += 1
                print()
                continue
            
            success = await download_file(page, name, token, output_dir)
            if success:
                ok += 1
        
        print(f"\n\n{'='*40}")
        print(f"✅ 完成！{ok}/{len(files)} 个视频")
        print(f"{'='*40}")
        
        total_size = 0
        for f in sorted(os.listdir(output_dir)):
            if f.endswith('.mp4'):
                fp = os.path.join(output_dir, f)
                mb = os.path.getsize(fp) / 1024 / 1024
                total_size += mb
                print(f"  {f}: {mb:.1f} MB")
        print(f"\n📊 总计: {total_size:.1f} MB")
        
        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())
