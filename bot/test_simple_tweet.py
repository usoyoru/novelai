import tweepy
import os
from dotenv import load_dotenv
import time

# 加载环境变量
load_dotenv()

try:
    # 创建客户端
    client = tweepy.Client(
        consumer_key=os.getenv("TWITTER_API_KEY"),
        consumer_secret=os.getenv("TWITTER_API_SECRET"),
        access_token=os.getenv("TWITTER_ACCESS_TOKEN"),
        access_token_secret=os.getenv("TWITTER_ACCESS_TOKEN_SECRET"),
        wait_on_rate_limit=True
    )
    
    # 获取用户信息
    me = client.get_me()
    print(f"✅ 已连接到账号: @{me.data.username}")
    
    # 发送测试推文
    response = client.create_tweet(text=f"测试推文 {int(time.time())}")
    tweet_id = response.data['id']
    print(f"✅ 推文发送成功！ID: {tweet_id}")
    print(f"访问: https://twitter.com/i/web/status/{tweet_id}")
    
    # 等待用户确认
    input("\n按回车键删除测试推文...")
    
    # 删除测试推文
    client.delete_tweet(tweet_id)
    print("✅ 测试推文已删除！")
    
except Exception as e:
    print(f"❌ 错误: {str(e)}")
    if "403 Forbidden" in str(e):
        print("\n这可能是因为：")
        print("1. 应用程序没有写入权限")
        print("2. 需要在开发者门户中启用 OAuth 1.0a")
        print("3. 需要重新生成访问令牌")
        print("\n请访问：")
        print("https://developer.twitter.com/en/portal/projects/")
        print("然后检查：")
        print("1. User authentication settings -> OAuth 1.0a")
        print("2. App permissions -> Read and Write")
        print("3. Keys and tokens -> Regenerate")
    else:
        print("\n可能的原因：")
        print("1. API密钥或令牌不正确")
        print("2. 账号没有足够的权限")
        print("3. 需要检查API访问级别设置") 