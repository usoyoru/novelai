import os
import asyncio
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.services.ai_service import AIService
from app.services.twitter_bot import TwitterBot
from app.models.novel import Novel, Chapter, PlotOption
from datetime import datetime

# 加载环境变量
load_dotenv()

async def generate_next_chapter():
    """基于投票结果生成下一章"""
    db = None
    try:
        # 初始化服务
        db = SessionLocal()
        ai_service = AIService()
        twitter_bot = TwitterBot(
            api_key=os.getenv("TWITTER_API_KEY"),
            api_secret=os.getenv("TWITTER_API_SECRET"),
            access_token=os.getenv("TWITTER_ACCESS_TOKEN"),
            access_token_secret=os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
        )

        # 获取最新的小说
        novel = db.query(Novel).order_by(Novel.id.desc()).first()
        if not novel:
            print("未找到小说记录")
            return

        print(f"\n当前小说: 《{novel.title}》")
        print(f"当前章节: 第{novel.current_chapter}章")

        # 获取获胜的投票选项
        winning_option = db.query(PlotOption).filter(
            PlotOption.novel_id == novel.id,
            PlotOption.chapter_number == novel.current_chapter,
            PlotOption.title == "寻找盟友"  # 获胜选项
        ).first()

        if not winning_option:
            print("未找到获胜选项")
            return

        print("\n获胜选项信息:")
        print(f"标题: {winning_option.title}")
        print(f"描述: {winning_option.description}")
        print(f"影响: {winning_option.impact}")

        # 获取上一章内容
        previous_chapter = db.query(Chapter).filter(
            Chapter.novel_id == novel.id,
            Chapter.chapter_number == novel.current_chapter
        ).first()

        if not previous_chapter:
            print("未找到上一章内容")
            return

        print("\n生成新章节...")
        # 生成新章节
        chapter_content = await ai_service.generate_next_chapter(
            title=novel.title,
            genre=novel.genre,
            outline=novel.outline,
            previous_chapter=previous_chapter.content,
            chosen_option=winning_option.__dict__,
            chapter_number=novel.current_chapter + 1
        )

        print("\n发布新章节到Twitter...")
        # 发布新章节
        tweet_id = twitter_bot.post_chapter(
            title=novel.title,
            chapter_number=novel.current_chapter + 1,
            content=chapter_content
        )

        # 保存新章节
        new_chapter = Chapter(
            novel_id=novel.id,
            chapter_number=novel.current_chapter + 1,
            content=chapter_content,
            tweet_id=tweet_id
        )
        db.add(new_chapter)

        print("\n生成新的投票选项...")
        # 生成下一章节的选项
        plot_options = await ai_service.generate_plot_options(
            title=novel.title,
            genre=novel.genre,
            current_chapter=chapter_content,
            outline=novel.outline
        )

        print("\n创建新的投票...")
        # 创建投票
        poll_tweet_id = twitter_bot.create_poll(
            title=novel.title,
            chapter_number=novel.current_chapter + 1,
            options=plot_options
        )

        # 保存选项
        for option in plot_options:
            new_option = PlotOption(
                novel_id=novel.id,
                chapter_number=novel.current_chapter + 1,
                option_id=option["option_id"],
                title=option["title"],
                description=option["description"],
                impact=option["impact"],
                tweet_id=poll_tweet_id
            )
            db.add(new_option)

        # 更新小说当前章节
        novel.current_chapter += 1
        db.commit()

        print("\n✅ 新章节生成完成！")
        print(f"章节推文: https://twitter.com/i/web/status/{tweet_id}")
        print(f"投票推文: https://twitter.com/i/web/status/{poll_tweet_id}")

    except Exception as e:
        print(f"\n❌ 错误: {str(e)}")
        if db:
            db.rollback()
    finally:
        if db:
            db.close()

if __name__ == "__main__":
    print("开始生成下一章...")
    asyncio.run(generate_next_chapter()) 