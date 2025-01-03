import os
from dotenv import load_dotenv
import tweepy

# 加载环境变量
load_dotenv()

def test_twitter_permissions():
    """测试 Twitter API 权限"""
    print("\n测试 Twitter API 权限...")
    
    try:
        # 1. 测试认证
        print("\n1. 测试认证...")
        auth = tweepy.OAuthHandler(
            os.getenv("TWITTER_API_KEY"),
            os.getenv("TWITTER_API_SECRET")
        )
        auth.set_access_token(
            os.getenv("TWITTER_ACCESS_TOKEN"),
            os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
        )
        
        api = tweepy.API(auth)
        client = tweepy.Client(
            consumer_key=os.getenv("TWITTER_API_KEY"),
            consumer_secret=os.getenv("TWITTER_API_SECRET"),
            access_token=os.getenv("TWITTER_ACCESS_TOKEN"),
            access_token_secret=os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
        )
        
        # 2. 获取账号信息
        print("\n2. 获取账号信息...")
        me = client.get_me()
        print(f"✅ 已连接到账号: @{me.data.username}")
        
        # 3. 测试读取权限
        print("\n3. 测试读取权限...")
        tweets = client.get_users_tweets(me.data.id, max_results=5)
        print("✅ 成功读取推文")
        
        # 4. 测试写入权限
        print("\n4. 测试写入权限...")
        response = client.create_tweet(text="这是一条测试推文，用于验证API权限。稍后会删除。")
        tweet_id = response.data['id']
        print("✅ 成功发送测试推文")
        
        # 5. 删除测试推文
        print("\n5. 删除测试推文...")
        client.delete_tweet(tweet_id)
        print("✅ 成功删除测试推文")
        
        print("\n✅ Twitter API 权限测试全部通过！")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        print("\n请检查：")
        print("1. API密钥和令牌是否正确")
        print("2. 应用程序是否有足够的权限")
        print("3. 开发者账号是否已获得必要的访问级别")

if __name__ == "__main__":
    print("开始 Twitter API 测试...")
    test_twitter_permissions() 