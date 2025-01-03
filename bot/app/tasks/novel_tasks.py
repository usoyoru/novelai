from datetime import datetime, timedelta, timezone
import logging
from sqlalchemy.orm import Session
from ..models.novel import Novel, Chapter, PlotOption
from ..services.ai_service import AIService, NovelPrompt
from sqlalchemy.sql import exists, and_

logger = logging.getLogger(__name__)

class NovelTasks:
    def __init__(self, db: Session, ai_service: AIService):
        """Initialize task processor"""
        self.db = db
        self.ai_service = ai_service
        logger.info("NovelTasks initialization completed")

    async def process_completed_polls(self):
        """Process completed polls"""
        try:
            logger.info("Starting to check completed polls...")
            
            # Get current time
            current_time = datetime.now(timezone.utc)
            
            # Get all unprocessed voting options (chapters without winners and created more than 10 minutes ago)
            unprocessed_options = self.db.query(PlotOption).filter(
                PlotOption.is_winner == False,
                PlotOption.created_at <= current_time - timedelta(minutes=10),  # Only process options created over 10 minutes ago
                ~exists().where(
                    and_(
                        Chapter.novel_id == PlotOption.novel_id,
                        Chapter.chapter_number == PlotOption.chapter_number + 1
                    )
                )
            ).all()
            
            if not unprocessed_options:
                logger.info("No pending polls found")
                return
            
            # Group options by chapter
            options_by_chapter = {}
            for option in unprocessed_options:
                key = (option.novel_id, option.chapter_number)
                if key not in options_by_chapter:
                    options_by_chapter[key] = []
                options_by_chapter[key].append(option)
            
            # Process votes for each chapter
            for (novel_id, chapter_number), options in options_by_chapter.items():
                # Get all votes for this chapter
                total_votes = sum(option.votes_count for option in options)
                
                if total_votes == 0:
                    # If no votes, randomly select an option
                    import random
                    winner = random.choice(options)
                    logger.info(f"No votes, randomly selected option: {winner.title}")
                else:
                    # Select option with most votes
                    winner = max(options, key=lambda x: x.votes_count)
                    logger.info(f"Option '{winner.title}' won with {winner.votes_count} votes")
                
                # Mark winning option
                winner.is_winner = True
                self.db.commit()
                
                # Get novel information
                novel = self.db.query(Novel).filter(Novel.id == novel_id).first()
                if not novel:
                    logger.error(f"Novel with ID {novel_id} not found")
                    continue
                
                # Get current chapter content
                current_chapter = self.db.query(Chapter).filter(
                    Chapter.novel_id == novel_id,
                    Chapter.chapter_number == chapter_number
                ).first()
                
                if not current_chapter:
                    logger.error(f"Chapter {chapter_number} not found for novel {novel.title}")
                    continue
                
                # Prepare to generate next chapter
                next_chapter_number = chapter_number + 1
                
                # Prepare winning option information
                chosen_option = {
                    "title": winner.title,
                    "description": winner.description,
                    "impact": winner.impact,
                    "votes": winner.votes_count
                }
                
                # Generate next chapter content
                logger.info(f"Starting to generate chapter {next_chapter_number}...")
                content = await self.ai_service.generate_next_chapter(
                    novel.title,
                    novel.genre,
                    novel.outline,
                    current_chapter.content,
                    chosen_option,
                    next_chapter_number
                )
                
                # Save new chapter
                new_chapter = Chapter(
                    novel_id=novel_id,
                    chapter_number=next_chapter_number,
                    content=content
                )
                self.db.add(new_chapter)
                self.db.commit()
                logger.info(f"Chapter {next_chapter_number} has been saved")
                
                # Update novel's current chapter number
                novel.current_chapter = next_chapter_number
                self.db.commit()
                
                # Generate voting options for new chapter
                await self.create_plot_options(novel, content, next_chapter_number)
                logger.info(f"Created voting options for chapter {next_chapter_number}")
                
        except Exception as e:
            logger.error(f"Error processing polls: {str(e)}")
            logger.exception("Detailed error information:")
            self.db.rollback()

    async def start_new_novel(self, title: str, genre: str):
        """Start a new novel"""
        try:
            logger.info("Generating novel outline...")
            outline = await self.ai_service.generate_outline(title, genre)
            logger.info("Outline generation completed")
            
            logger.info("Saving novel information to database...")
            novel = Novel(
                title=title,
                genre=genre,
                outline=outline,
                current_chapter=1
            )
            self.db.add(novel)
            self.db.commit()
            logger.info(f"Novel information saved, ID: {novel.id}")
            
            # Generate first chapter
            logger.info("Generating first chapter content...")
            prompt = NovelPrompt(
                title=title,
                genre=genre,
                outline=outline,
                chapter_number=1
            )
            content = await self.ai_service.generate_chapter(prompt)
            logger.info("First chapter content generated")
            
            # Save first chapter
            logger.info("Saving first chapter to database...")
            chapter = Chapter(
                novel_id=novel.id,
                chapter_number=1,
                content=content
            )
            self.db.add(chapter)
            self.db.commit()
            logger.info("First chapter saved to database")
            
            # Generate voting options for first chapter
            await self.create_plot_options(novel, content, 1)
            logger.info("Voting options created for first chapter")
            
        except Exception as e:
            logger.error(f"Error creating new novel: {str(e)}")
            logger.exception("Detailed error information:")
            self.db.rollback()
            raise

    async def create_plot_options(self, novel, chapter_content: str, chapter_number: int):
        """Create voting options for chapter"""
        try:
            logger.info(f"Generating voting options for chapter {chapter_number}...")
            
            # Delete old voting options for this chapter
            self.db.query(PlotOption).filter(
                PlotOption.novel_id == novel.id,
                PlotOption.chapter_number == chapter_number
            ).delete()
            self.db.commit()
            
            # Generate voting options
            plot_options = await self.ai_service.generate_plot_options(
                title=novel.title,
                genre=novel.genre,
                current_chapter=chapter_content,
                outline=novel.outline
            )
            
            # Save voting options
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
            logger.info(f"Created {len(plot_options)} voting options for chapter {chapter_number}")
            
        except Exception as e:
            logger.error(f"Error creating voting options: {str(e)}")
            logger.exception("Detailed error information:")
            self.db.rollback()
            raise 

    async def generate_chapter_with_options(self, novel_id: int, chapter_number: int):
        """Generate voting options for specified chapter"""
        try:
            # Get novel information
            novel = self.db.query(Novel).filter(Novel.id == novel_id).first()
            if not novel:
                logger.error(f"Novel with ID {novel_id} not found")
                return
            
            # Get chapter content
            chapter = self.db.query(Chapter).filter(
                Chapter.novel_id == novel_id,
                Chapter.chapter_number == chapter_number
            ).first()
            
            if not chapter:
                logger.error(f"Chapter {chapter_number} not found for novel {novel.title}")
                return
            
            # Check if voting options already exist
            existing_options = self.db.query(PlotOption).filter(
                PlotOption.novel_id == novel_id,
                PlotOption.chapter_number == chapter_number
            ).count()
            
            if existing_options > 0:
                logger.info(f"Chapter {chapter_number} already has voting options")
                return
            
            # Generate new voting options
            await self.create_plot_options(novel, chapter.content, chapter_number)
            logger.info(f"Generated voting options for chapter {chapter_number}")
            
        except Exception as e:
            logger.error(f"Error generating chapter voting options: {str(e)}")
            logger.exception("Detailed error information:")
            self.db.rollback()
            raise 