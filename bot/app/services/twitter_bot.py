import tweepy
import logging
from typing import List, Dict
import time
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

logger = logging.getLogger(__name__)

class TwitterBot:
    def __init__(self):
        """初始化Twitter机器人"""
        try:
            # 从环境变量获取认证信息
            self.client = tweepy.Client(
                consumer_key=os.getenv("TWITTER_API_KEY"),
                consumer_secret=os.getenv("TWITTER_API_SECRET"),
                access_token=os.getenv("TWITTER_ACCESS_TOKEN"),
                access_token_secret=os.getenv("TWITTER_ACCESS_TOKEN_SECRET"),
                bearer_token=os.getenv("TWITTER_BEARER_TOKEN"),
                wait_on_rate_limit=True
            )
            
            # 验证连接和权限
            self._verify_credentials()
            
            me = self.client.get_me()
            logger.info(f"Connected to Twitter as @{me.data.username}")
        except Exception as e:
            logger.error(f"Failed to initialize Twitter bot: {str(e)}")
            raise

    def _verify_credentials(self):
        """验证Twitter API的权限"""
        try:
            # 检查是否有读取权限
            me = self.client.get_me()
            if not me:
                raise Exception("无法获取账户信息")
                
            # 尝试发送测试推文（稍后会删除）
            test_tweet = self.client.create_tweet(text="Testing API permissions...")
            if test_tweet:
                # 删除测试推文
                self.client.delete_tweet(test_tweet.data['id'])
                logger.info("Twitter API权限验证成功")
            else:
                raise Exception("无法发送测试推文")
                
        except Exception as e:
            logger.error(f"Twitter API权限验证失败: {str(e)}")
            raise

    def get_tweet_with_poll(self, tweet_id: str) -> dict:
        """获取带投票的推文"""
        try:
            tweet = self.client.get_tweet(
                tweet_id,
                expansions=['attachments.poll_ids'],
                poll_fields=['options', 'voting_status', 'end_datetime']
            )
            return tweet
        except Exception as e:
            logger.error(f"Error getting tweet: {str(e)}")
            raise

    def post_chapter(self, title: str, chapter_number: int, content: str, max_retries: int = 3) -> str:
        """发布章节内容到Twitter"""
        retry_count = 0
        while retry_count < max_retries:
            try:
                # 分割内容为多条推文
                tweets = self._split_content(content)
                
                # 发送第一条推文（包含标题）
                first_tweet = f"《{title}》第{chapter_number}章\n\n{tweets[0]}"
                response = self.client.create_tweet(text=first_tweet)
                previous_id = response.data['id']
                
                # 发送剩余的推文
                for tweet in tweets[1:]:
                    response = self.client.create_tweet(
                        text=tweet,
                        in_reply_to_tweet_id=previous_id
                    )
                    previous_id = response.data['id']
                
                logger.info(f"Successfully posted chapter {chapter_number}")
                return str(previous_id)
                
            except tweepy.errors.Forbidden as e:
                retry_count += 1
                logger.warning(f"发推文权限错误 (尝试 {retry_count}/{max_retries}): {str(e)}")
                if retry_count >= max_retries:
                    logger.error("发推文失败，已达到最大重试次数")
                    raise
                time.sleep(5)  # 等待5秒后重试
                
            except tweepy.errors.TweepyException as e:
                retry_count += 1
                logger.warning(f"Twitter API错误 (尝试 {retry_count}/{max_retries}): {str(e)}")
                if retry_count >= max_retries:
                    logger.error("发推文失败，已达到最大重试次数")
                    raise
                time.sleep(5)  # 等待5秒后重试
                
            except Exception as e:
                logger.error(f"Error posting chapter: {str(e)}")
                raise

    def create_poll(self, title: str, chapter_number: int, options: List[Dict]) -> str:
        """发布选项，返回推文ID"""
        try:
            # 发布主推文
            main_text = f"《{title}》第{chapter_number}章 - 剧情选择 (5分钟测试投票)"
            response = self.client.create_tweet(
                text=main_text,
                poll_options=[opt["title"] for opt in options[:4]],
                poll_duration_minutes=5  # 设置为5分钟
            )
            main_tweet_id = response.data['id']
            previous_tweet_id = main_tweet_id
            
            # 发布选项详情
            for opt in options[:4]:
                option_text = f"{opt['option_id']}. {opt['description']}\n影响: {opt['impact']}"
                response = self.client.create_tweet(
                    text=option_text,
                    in_reply_to_tweet_id=previous_tweet_id
                )
                previous_tweet_id = response.data['id']
                time.sleep(1)
            
            return str(main_tweet_id)
            
        except Exception as e:
            logger.error(f"Error creating poll: {str(e)}")
            raise

    def _split_content(self, content: str, max_length: int = 270) -> List[str]:
        """将内容分割成适合推文长度的片段"""
        tweets = []
        paragraphs = content.split('\n\n')
        current_tweet = ""
        
        for paragraph in paragraphs:
            if len(current_tweet) + len(paragraph) + 2 <= max_length:
                if current_tweet:
                    current_tweet += "\n\n"
                current_tweet += paragraph
            else:
                if current_tweet:
                    tweets.append(current_tweet)
                current_tweet = paragraph
                
        if current_tweet:
            tweets.append(current_tweet)
            
        return tweets 