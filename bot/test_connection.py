import os
from dotenv import load_dotenv
from openai import OpenAI
import tweepy
import asyncio

# 加载环境变量
load_dotenv()

async def test_openai():
    """测试 OpenAI API 连接"""
    print("\n测试 OpenAI API 连接...")
    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "你是一个小说家。"},
                {"role": "user", "content": "写一个简短的故事开头（100字以内）"}
            ],
            max_tokens=200
        )
        print("✅ OpenAI API 连接成功！")
        print("生成的内容示例：")
        print(response.choices[0].message.content)
    except Exception as e:
        print("❌ OpenAI API 连接失败：", str(e))

def test_twitter():
    """测试 Twitter API 连接"""
    print("\n测试 Twitter API 连接...")
    try:
        # 验证凭据
        auth = tweepy.OAuthHandler(
            os.getenv("TWITTER_API_KEY"),
            os.getenv("TWITTER_API_SECRET")
        )
        auth.set_access_token(
            os.getenv("TWITTER_ACCESS_TOKEN"),
            os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
        )
        
        # 创建API客户端
        api = tweepy.API(auth)
        client = tweepy.Client(
            consumer_key=os.getenv("TWITTER_API_KEY"),
            consumer_secret=os.getenv("TWITTER_API_SECRET"),
            access_token=os.getenv("TWITTER_ACCESS_TOKEN"),
            access_token_secret=os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
        )
        
        # 获取用户信息
        me = client.get_me()
        print("✅ Twitter API 连接成功！")
        print(f"已连接到Twitter账号: @{me.data.username}")
        
        # 发送测试推文
        response = client.create_tweet(text="这是一条测试推文，稍后会删除。")
        tweet_id = response.data['id']
        print("✅ 测试推文发送成功！")
        
        # 删除测试推文
        client.delete_tweet(tweet_id)
        print("✅ 测试推文已删除！")
        
    except Exception as e:
        print("❌ Twitter API 连接失败：", str(e))

async def main():
    # 测试 OpenAI API
    await test_openai()
    
    # 测试 Twitter API
    test_twitter()

if __name__ == "__main__":
    print("开��API连接测试...")
    asyncio.run(main()) 