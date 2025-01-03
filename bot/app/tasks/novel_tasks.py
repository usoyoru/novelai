from datetime import datetime, timedelta, timezone
import logging
from sqlalchemy.orm import Session
from ..models.novel import Novel, Chapter, PlotOption
from ..services.ai_service import AIService, NovelPrompt
from sqlalchemy.sql import exists, and_

logger = logging.getLogger(__name__)

class NovelTasks:
    def __init__(self, db: Session, ai_service: AIService):
        """初始化任务处理器"""
        self.db = db
        self.ai_service = ai_service
        logger.info("NovelTasks初始化完成")

    async def process_completed_polls(self):
        """处理已完成的投票"""
        try:
            logger.info("开始检查已完成的投票...")
            
            # 获取当前时间
            current_time = datetime.now(timezone.utc)
            
            # 获取所有未处理的投票选项（没有获胜者的章节，且创建时间超过10分钟）
            unprocessed_options = self.db.query(PlotOption).filter(
                PlotOption.is_winner == False,
                PlotOption.created_at <= current_time - timedelta(minutes=10),  # 只处理创建超过10分钟的投票
                ~exists().where(
                    and_(
                        Chapter.novel_id == PlotOption.novel_id,
                        Chapter.chapter_number == PlotOption.chapter_number + 1
                    )
                )
            ).all()
            
            if not unprocessed_options:
                logger.info("没有找到待处理的投票")
                return
            
            # 按章节分组
            options_by_chapter = {}
            for option in unprocessed_options:
                key = (option.novel_id, option.chapter_number)
                if key not in options_by_chapter:
                    options_by_chapter[key] = []
                options_by_chapter[key].append(option)
            
            # 处理每个章节的投票
            for (novel_id, chapter_number), options in options_by_chapter.items():
                # 获取该章节的所有投票
                total_votes = sum(option.votes_count for option in options)
                
                if total_votes == 0:
                    # 如果没有投票，随机选择一个选项
                    import random
                    winner = random.choice(options)
                    logger.info(f"没有投票，随机选择选项: {winner.title}")
                else:
                    # 选择得票最多的选项
                    winner = max(options, key=lambda x: x.votes_count)
                    logger.info(f"选项 '{winner.title}' 获胜，得票数: {winner.votes_count}")
                
                # 标记获胜选项
                winner.is_winner = True
                self.db.commit()
                
                # 获取小说信息
                novel = self.db.query(Novel).filter(Novel.id == novel_id).first()
                if not novel:
                    logger.error(f"找不到ID为 {novel_id} 的小说")
                    continue
                
                # 获取当前章节内容
                current_chapter = self.db.query(Chapter).filter(
                    Chapter.novel_id == novel_id,
                    Chapter.chapter_number == chapter_number
                ).first()
                
                if not current_chapter:
                    logger.error(f"找不到小说 {novel.title} 的第 {chapter_number} 章")
                    continue
                
                # 准备生成下一章
                next_chapter_number = chapter_number + 1
                
                # 构造获胜选项的信息
                chosen_option = {
                    "title": winner.title,
                    "description": winner.description,
                    "impact": winner.impact,
                    "votes": winner.votes_count
                }
                
                # 生成下一章内容
                logger.info(f"开始生成第 {next_chapter_number} 章...")
                content = await self.ai_service.generate_next_chapter(
                    novel.title,
                    novel.genre,
                    novel.outline,
                    current_chapter.content,
                    chosen_option,
                    next_chapter_number
                )
                
                # 保存新章节
                new_chapter = Chapter(
                    novel_id=novel_id,
                    chapter_number=next_chapter_number,
                    content=content
                )
                self.db.add(new_chapter)
                self.db.commit()
                logger.info(f"第 {next_chapter_number} 章已保存")
                
                # 更新小说的当前章节号
                novel.current_chapter = next_chapter_number
                self.db.commit()
                
                # 为新章节生成投票选项
                await self.create_plot_options(novel, content, next_chapter_number)
                logger.info(f"已为第 {next_chapter_number} 章创建投票选项")
                
        except Exception as e:
            logger.error(f"处理投票时出错: {str(e)}")
            logger.exception("详细错误信息:")
            self.db.rollback()

    async def start_new_novel(self, title: str, genre: str):
        """开始一个新的小说"""
        try:
            logger.info("正在生成小说大纲...")
            outline = await self.ai_service.generate_outline(title, genre)
            logger.info("大纲生成完成")
            
            logger.info("正在保存小说信息到数据库...")
            novel = Novel(
                title=title,
                genre=genre,
                outline=outline,
                current_chapter=1
            )
            self.db.add(novel)
            self.db.commit()
            logger.info(f"小说信息已保存，ID: {novel.id}")
            
            # 生成第一章
            logger.info("正在生成第一章内容...")
            prompt = NovelPrompt(
                title=title,
                genre=genre,
                outline=outline,
                chapter_number=1
            )
            content = await self.ai_service.generate_chapter(prompt)
            logger.info("第一章内容生成完成")
            
            # 保存第一章
            logger.info("正在保存第一章到数据库...")
            chapter = Chapter(
                novel_id=novel.id,
                chapter_number=1,
                content=content
            )
            self.db.add(chapter)
            self.db.commit()
            logger.info("第一章已保存到数据库")
            
            # 生成第一章的投票选项
            await self.create_plot_options(novel, content, 1)
            logger.info("第一章的投票选项已创建")
            
        except Exception as e:
            logger.error(f"创建新小说时出错: {str(e)}")
            logger.exception("详细错误信息:")
            self.db.rollback()
            raise

    async def create_plot_options(self, novel, chapter_content: str, chapter_number: int):
        """为章节创建投票选项"""
        try:
            logger.info(f"正在为第 {chapter_number} 章生成投票选项...")
            
            # 删除该章节的旧投票选项
            self.db.query(PlotOption).filter(
                PlotOption.novel_id == novel.id,
                PlotOption.chapter_number == chapter_number
            ).delete()
            self.db.commit()
            
            # 生成投票选项
            plot_options = await self.ai_service.generate_plot_options(
                title=novel.title,
                genre=novel.genre,
                current_chapter=chapter_content,
                outline=novel.outline
            )
            
            # 保存投票选项
            for option in plot_options:
                new_option = PlotOption(
                    novel_id=novel.id,
                    chapter_number=chapter_number,
                    option_id=option["option_id"],
                    title=option["title"],
                    description=option["description"],
                    impact=option["impact"]
                )
                self.db.add(new_option)
            
            self.db.commit()
            logger.info(f"已为第 {chapter_number} 章创建 {len(plot_options)} 个投票选项")
            
        except Exception as e:
            logger.error(f"创建投票选项时出错: {str(e)}")
            logger.exception("详细错误信息:")
            self.db.rollback()
            raise 

    async def generate_chapter_with_options(self, novel_id: int, chapter_number: int):
        """生成指定章节的投票选项"""
        try:
            # 获取小说信息
            novel = self.db.query(Novel).filter(Novel.id == novel_id).first()
            if not novel:
                logger.error(f"找不到ID为 {novel_id} 的小说")
                return
            
            # 获取章节内容
            chapter = self.db.query(Chapter).filter(
                Chapter.novel_id == novel_id,
                Chapter.chapter_number == chapter_number
            ).first()
            
            if not chapter:
                logger.error(f"找不到小说 {novel.title} 的第 {chapter_number} 章")
                return
            
            # 检查是否已经有投票选项
            existing_options = self.db.query(PlotOption).filter(
                PlotOption.novel_id == novel_id,
                PlotOption.chapter_number == chapter_number
            ).count()
            
            if existing_options > 0:
                logger.info(f"第 {chapter_number} 章已经有投票选项")
                return
            
            # 生成新的投票选项
            await self.create_plot_options(novel, chapter.content, chapter_number)
            logger.info(f"已为第 {chapter_number} 章生成投票选项")
            
        except Exception as e:
            logger.error(f"生成章节投票选项时出错: {str(e)}")
            logger.exception("详细错误信息:")
            self.db.rollback()
            raise 