import asyncio
import os
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.services.ai_service import AIService
from app.services.twitter_bot import TwitterBot
from app.tasks.novel_tasks import NovelTasks
from app.models.novel import Novel, Chapter, PlotOption
import time

# 加载环境变量
load_dotenv()

async def test_novel_flow():
    """测试完整的小说生成和投票流程"""
    print("\n开始测试小说生成流程...")
    
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
        novel_tasks = NovelTasks(db, ai_service, twitter_bot)
        
        # 1. 开始新小说
        print("\n1. 创建新小说...")
        title = f"星际迷航：未知边界 {int(time.time())}"  # 添加时间戳避免重复
        genre = "科幻冒险"
        novel = await novel_tasks.start_new_novel(title, genre)
        print(f"✅ 小说《{title}》创建成功！")
        print(f"- ID: {novel.id}")
        print(f"- 类型: {novel.genre}")
        print(f"- 大纲预览: {novel.outline[:200]}...")
        
        # 2. 获取第一章内容
        print("\n2. 获取第一章内容...")
        chapter = db.query(Chapter).filter(
            Chapter.novel_id == novel.id,
            Chapter.chapter_number == 1
        ).first()
        print("✅ 第一章生成成功！")
        print(f"- 内容预览: {chapter.content[:200]}...")
        print(f"- Tweet ID: {chapter.tweet_id}")
        print(f"- 访问: https://twitter.com/i/web/status/{chapter.tweet_id}")
        
        # 3. 获取投票选项
        print("\n3. 获取投票选项...")
        plot_options = db.query(PlotOption).filter(
            PlotOption.novel_id == novel.id,
            PlotOption.chapter_number == 1
        ).all()
        print("✅ 投票选项生成成功！")
        for option in plot_options:
            print(f"\n选项 {option.option_id}:")
            print(f"- 标题: {option.title}")
            print(f"- 描述: {option.description}")
            print(f"- 影响: {option.impact}")
            print(f"- Tweet ID: {option.tweet_id}")
            print(f"- 访问: https://twitter.com/i/web/status/{option.tweet_id}")
        
        print("\n✅ 完整流程测试成功！")
        print("\n提示：")
        print("1. 请在Twitter上查看发布的内容")
        print("2. 24小时后，机器人会自动处理投票结果并生成新章节")
        print("3. 你也可以手动运行 process_completed_polls() 来测试投票处理")
        
        # 等待用户确认
        input("\n按回车键继续...")
        
    except Exception as e:
        print(f"\n❌ 测试过程中出错: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    print("开始完整流程测试...")
    asyncio.run(test_novel_flow()) 