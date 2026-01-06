import yt_dlp
import json
import os

def download_video(url):
    # 检查是否存在 cookies.txt（使用绝对路径避免工作目录问题）
    script_dir = os.path.dirname(os.path.abspath(__file__))
    cookie_path = os.path.join(script_dir, 'cookies.txt')
    use_cookie = os.path.isfile(cookie_path)

    if use_cookie:
        print(f"🍪 检测到 {cookie_path}，将携带 Cookie 访问...")
    else:
        print("⚠️ 未检测到 cookies.txt，抖音等平台可能会失败。")

    # 配置选项
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'outtmpl': '%(title)s.%(ext)s',
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }
    
    # 动态添加 cookiefile 参数
    if use_cookie:
        ydl_opts['cookiefile'] = cookie_path
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print(f"🔍 正在解析链接: {url} ...")
            
            # 1. 解析视频信息 (不下载)
            info_dict = ydl.extract_info(url, download=False)
            
            video_title = info_dict.get('title', '未知标题')
            uploader = info_dict.get('uploader', '未知作者')
            view_count = info_dict.get('view_count', 0)
            
            print("-" * 30)
            print(f"✅ 解析成功！")
            print(f"🎬 标题: {video_title}")
            print(f"👤 作者: {uploader}")
            print(f"👁️ 播放量: {view_count}")
            print("-" * 30)

            # 2. 开始下载
            confirm = input("🚀 确认下载吗? (y/n): ").strip().lower()
            if confirm == 'y':
                print("⬇️  开始下载中，请稍候...")
                ydl.download([url])
                print(f"🎉 下载完成！文件已保存为: {video_title}.{info_dict.get('ext')}")
            else:
                print("🚫 已取消下载。")

    except Exception as e:
        print(f"❌ 发生错误: {e}")
        print("提示：如果是B站/小红书，可能需要配置 Cookies 或链接已失效。")

if __name__ == "__main__":
    print("支持 Bilibili / 抖音 / 小红书(部分) / YouTube 等")
    target_url = input("👉 请输入视频链接: ").strip()
    
    if target_url:
        download_video(target_url)
    else:
        print("❌ 未输入链接")