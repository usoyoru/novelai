from typing import List, Optional
import os
import logging
import json
from openai import OpenAI
from pydantic import BaseModel

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NovelPrompt(BaseModel):
    title: Optional[str] = None
    genre: Optional[str] = None
    outline: Optional[str] = None
    characters: Optional[List[str]] = None
    chapter_number: Optional[int] = None
    previous_content: Optional[str] = None
    word_count: Optional[int] = 2000

class AIService:
    def __init__(self):
        """初始化AI服务"""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("未设置 OPENAI_API_KEY 环境变量")
        
        self.client = OpenAI(api_key=api_key)
        logger.info("AI服务初始化完成")

    async def generate_outline(self, title: str, genre: str) -> str:
        try:
            logger.info(f"Generating outline for title: {title}, genre: {genre}")
            
            prompt = f"""As a professional novel outline planner, please create a detailed story outline for a novel titled "{title}" in the {genre} genre. This is a cryptocurrency-themed novel with American writing style.

            The outline should include:
            1. Story Background:
               - Time period (Cryptocurrency market in Silicon Valley/Wall Street)
               - Market environment (Bull/Bear markets, regulations, major events)
               - Main locations (New York, San Francisco, Miami, and other US fintech hubs)

            2. Main Characters:
               - Protagonist (Young ambitious trader/entrepreneur/investor with strong personality)
               - Supporting characters (Wall Street elites, Silicon Valley tech moguls, government regulators)
               - Character relationships (Dynamic competition and cooperation)

            3. Core Conflicts:
               - Main conflicts (Innovation vs. Regulation, Ideals vs. Reality)
               - Market battles (Thrilling long vs. short positions, life-or-death project competition)
               - Personal challenges (Moral vs. Profit, Trust vs. Betrayal)

            4. Plot Development (at least 5 key points):
               - Fast-paced market turning points
               - Dramatic project development twists
               - Intense character confrontations
               - Unexpected crisis events
               - Climactic decision moments

            5. Ending:
               - Thrilling final showdown
               - Unexpected plot twist
               - Intriguing future implications

            Writing Style Requirements:
            1. American Writing Style:
               - Fast pace, tight plot
               - Sharp, punchy dialogue
               - Vivid scene descriptions
               - Direct conflicts
            2. American Financial Culture:
               - Wall Street terminology
               - Silicon Valley startup culture
               - US regulatory environment
            3. Dramatic and Entertaining:
               - Thrilling plot twists
               - Engaging character conflicts
               - Unexpected developments"""

            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a skilled novel planner specializing in American-style writing, focused on creating fast-paced, conflict-driven stories."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=2000
            )
            logger.info("Successfully generated outline")
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error generating outline: {str(e)}")
            raise

    async def generate_chapter(self, prompt: NovelPrompt) -> str:
        try:
            logger.info(f"Generating chapter for title: {prompt.title}")
            
            context = f"""Title: "{prompt.title}"
            Genre: {prompt.genre}
            Outline: {prompt.outline}
            Chapter: {prompt.chapter_number}
            Previous Content: {prompt.previous_content if prompt.previous_content else 'This is the first chapter'}
            
            Please write this chapter in American style with the following requirements:
            1. Word count: around {prompt.word_count} words
            2. Writing Style:
               - Hook readers from the start
               - Sharp, impactful dialogue
               - Vivid scene descriptions
               - Fast-paced, intense rhythm
            3. Content Features:
               - Use American financial and tech terminology
               - Showcase Wall Street/Silicon Valley culture
               - Emphasize market dynamics
            4. Plot Design:
               - Every scene must have conflict
               - Dialogue drives the plot
               - Create suspense and twists
            5. Character Development:
               - Strong, distinct personalities
               - Decisive actions
               - Deep inner thoughts
            6. Professional Content:
               - Accurate market analysis
               - Clear technical descriptions
               - Realistic financial operations
            7. Scene Description:
               - Intense trading scenes
               - High-stakes negotiations
               - Dramatic decision moments
            8. Chapter Ending:
               - Plant seeds for next chapter
               - Create compelling cliffhangers
               - Maintain reader anticipation"""

            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a skilled novelist specializing in American-style writing, focused on creating fast-paced, conflict-driven stories."},
                    {"role": "user", "content": context}
                ],
                temperature=0.7,
                max_tokens=3000
            )
            logger.info("Successfully generated chapter")
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error generating chapter: {str(e)}")
            raise

    async def generate_plot_options(self, title: str, genre: str, current_chapter: str, outline: str) -> List[dict]:
        try:
            logger.info(f"Generating plot options for title: {title}")
            
            prompt = f"""As a professional novel planner, please generate 4 different plot options for the novel "{title}".

            Current Context:
            Genre: {genre}
            Outline: {outline}
            Current Chapter Content: {current_chapter[:500]}...

            Please generate 4 options, each containing:
            1. Option title (brief)
            2. Option description (specific plot direction)
            3. Impact (how this choice affects the story)

            Output in strict JSON format as follows:
            [
                {{
                    "option_id": "A",
                    "title": "Option Title",
                    "description": "Option Description",
                    "impact": "Choice Impact"
                }},
                {{
                    "option_id": "B",
                    "title": "Option Title",
                    "description": "Option Description",
                    "impact": "Choice Impact"
                }},
                {{
                    "option_id": "C",
                    "title": "Option Title",
                    "description": "Option Description",
                    "impact": "Choice Impact"
                }},
                {{
                    "option_id": "D",
                    "title": "Option Title",
                    "description": "Option Description",
                    "impact": "Choice Impact"
                }}
            ]

            Notes:
            1. Must follow the exact JSON format above
            2. Do not add any extra text
            3. Ensure JSON format is correct"""

            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a skilled novel planner specializing in creating engaging plot options. Your output must be in strict JSON format."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=2000
            )
            
            content = response.choices[0].message.content
            logger.info(f"Generated content: {content[:200]}...")  # 记录生成的内容的前200个字符
            
            try:
                # 尝试清理和格式化内容
                content = content.strip()
                if not content.startswith('['):
                    # 尝试找到JSON数组的开始位置
                    start = content.find('[')
                    if start != -1:
                        content = content[start:]
                if not content.endswith(']'):
                    # 尝试找到JSON数组的结束位置
                    end = content.rfind(']')
                    if end != -1:
                        content = content[:end+1]
                
                # 解析JSON
                options = json.loads(content)
                
                # 验证选项格式
                if not isinstance(options, list):
                    raise ValueError("选项必须是一个数组")
                
                for option in options:
                    if not all(key in option for key in ['option_id', 'title', 'description', 'impact']):
                        raise ValueError("选项格式不正确")
                
                logger.info("Successfully generated plot options")
                return options
                
            except json.JSONDecodeError as e:
                logger.error(f"JSON parsing error: {str(e)}")
                logger.error(f"Content causing error: {content}")
                # 返回默认选项
                return [
                    {
                        "option_id": "A",
                        "title": "继续探索",
                        "description": "深入探索未知区域，寻找更多线索。",
                        "impact": "可能发现重要信息，但也可能遭遇危险。"
                    },
                    {
                        "option_id": "B",
                        "title": "返回基地",
                        "description": "先返回基地补给和汇报情况。",
                        "impact": "确保安全，但可能错过重要机会。"
                    },
                    {
                        "option_id": "C",
                        "title": "寻求支援",
                        "description": "联系附近的盟友寻求帮助。",
                        "impact": "增加成功的机会，但需要等待时间。"
                    },
                    {
                        "option_id": "D",
                        "title": "改变计划",
                        "description": "尝试一个新的解决方案。",
                        "impact": "可能带来意想不到的转机。"
                    }
                ]
            
        except Exception as e:
            logger.error(f"Error generating plot options: {str(e)}")
            raise

    async def generate_next_chapter(self, title: str, genre: str, outline: str, previous_chapter: str, chosen_option: dict, chapter_number: int) -> str:
        """根据选定的选项生成下一章节"""
        try:
            logger.info(f"Generating chapter {chapter_number} based on chosen option")
            
            prompt = f"""请为小说《{title}》({genre})创作第{chapter_number}章。

            前情提要：
            {previous_chapter[:500]}...

            读者投票选择的剧情发展：
            标题：{chosen_option['title']}
            描述：{chosen_option['description']}
            影响：{chosen_option['impact']}
            得票：{chosen_option['votes']}票

            整体大纲：
            {outline}

            要求：
            1. 字数在2000字左右
            2. 要自然地承接上一章节
            3. 要体现读者选择的剧情发展
            4. 要为下一章留下悬念
            5. 保持人物性格的连贯性
            6. 注意故事节奏的把控
            7. 细致描写场景和人物心理
            8. 增加适当的对话和互动
            """

            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "你是一个专业的小说家，擅长根据读者选择创作引人入胜的故事。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=3000
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"Error generating next chapter: {str(e)}")
            raise 