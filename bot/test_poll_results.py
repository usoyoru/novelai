import os
from dotenv import load_dotenv
import tweepy
from datetime import datetime, timezone

# 加载环境变量
load_dotenv()

def check_tweet():
    """检查推文基本信息"""
    try:
        # 使用Bearer Token创建客户端
        client = tweepy.Client(
            bearer_token=os.getenv("TWITTER_BEARER_TOKEN"),
            consumer_key=os.getenv("TWITTER_API_KEY"),
            consumer_secret=os.getenv("TWITTER_API_SECRET"),
            access_token=os.getenv("TWITTER_ACCESS_TOKEN"),
            access_token_secret=os.getenv("TWITTER_ACCESS_TOKEN_SECRET"),
            wait_on_rate_limit=True
        )
        
        # 获取推文
        tweet_id = "1871362824905302386"
        tweet = client.get_tweet(
            tweet_id,
            tweet_fields=['created_at', 'public_metrics', 'text'],
            expansions=['author_id', 'attachments.poll_ids'],
            poll_fields=['duration_minutes', 'end_datetime', 'id', 'options', 'voting_status']
        )
        
        if tweet and tweet.data:
            print("\n推文信息:")
            print(f"内容: {tweet.data.text}")
            print(f"发布时间: {tweet.data.created_at}")
            
            # 获取公开指标
            if hasattr(tweet.data, 'public_metrics'):
                metrics = tweet.data.public_metrics
                print("\n互动数据:")
                print(f"回复数: {metrics.get('reply_count', 0)}")
                print(f"转发数: {metrics.get('retweet_count', 0)}")
                print(f"点赞数: {metrics.get('like_count', 0)}")
                print(f"引用数: {metrics.get('quote_count', 0)}")
            
            # 获取投票信息
            if hasattr(tweet, 'includes') and 'polls' in tweet.includes:
                poll = tweet.includes['polls'][0]
                print("\n投票信息:")
                print(f"投票状态: {'进行中' if poll.voting_status == 'open' else '已结束'}")
                print(f"结束时间: {poll.end_datetime}")
                
                # 计算投票是否已结束
                now = datetime.now(timezone.utc)
                time_diff = now - poll.end_datetime
                minutes_passed = time_diff.total_seconds() / 60
                
                print(f"\n已经过去: {abs(minutes_passed):.1f}分钟")
                if minutes_passed > 0:
                    print("投票已结束")
                else:
                    print(f"投票还在进行中，还剩 {abs(minutes_passed):.1f} 分钟")
                
                print("\n投票选项:")
                total_votes = 0
                for option in poll.options:
                    votes = option['votes']
                    total_votes += votes
                    print(f"- {option['label']}: {votes}票")
                
                print(f"\n总投票数: {total_votes}票")
                
                # 如果投票已结束，显示获胜选项
                if minutes_passed > 0 and total_votes > 0:
                    winner = max(poll.options, key=lambda x: x['votes'])
                    print(f"\n获胜选项: {winner['label']} ({winner['votes']}票)")
            else:
                print("\n未找到投票信息")
            
    except Exception as e:
        print(f"\n❌ 错误: {str(e)}")
        if "401 Unauthorized" in str(e):
            print("\n认证错误，请检查:")
            print("1. Bearer Token 是否正确")
            print("2. API密钥和令牌是否正确")
        elif "403 Forbidden" in str(e):
            print("\nAPI访问受限，请检查:")
            print("1. API访问级别是否足够")
            print("2. 是否有必要的权限")
            print("\n建议访问: https://developer.twitter.com/en/portal/products")
        else:
            print("\n其他错误，请检查:")
            print("1. 推文ID是否正确")
            print("2. 推文是否已被删除")
            print("3. 网络连接是否正常")

if __name__ == "__main__":
    print("开始获取推文信息...")
    check_tweet() 