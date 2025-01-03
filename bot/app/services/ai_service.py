from typing import List, Optional
import os
import logging
import json
from openai import OpenAI
from pydantic import BaseModel

# Configure logging
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
        """Initialize AI service"""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.proxyapi.us/v1"  # 使用代理 API 端点
        )
        logger.info("AI service initialization completed")

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
            logger.info(f"Generated content: {content[:200]}...")  # Log first 200 characters of generated content
            
            try:
                # Try to clean and format content
                content = content.strip()
                if not content.startswith('['):
                    # Try to find the start of JSON array
                    start = content.find('[')
                    if start != -1:
                        content = content[start:]
                if not content.endswith(']'):
                    # Try to find the end of JSON array
                    end = content.rfind(']')
                    if end != -1:
                        content = content[:end+1]
                
                # Parse JSON
                options = json.loads(content)
                
                # Validate options format
                if not isinstance(options, list):
                    raise ValueError("Options must be an array")
                
                for option in options:
                    if not all(key in option for key in ['option_id', 'title', 'description', 'impact']):
                        raise ValueError("Invalid option format")
                
                logger.info("Successfully generated plot options")
                return options
                
            except json.JSONDecodeError as e:
                logger.error(f"JSON parsing error: {str(e)}")
                logger.error(f"Content causing error: {content}")
                # Return default options
                return [
                    {
                        "option_id": "A",
                        "title": "Continue Exploration",
                        "description": "Explore unknown areas and search for more clues.",
                        "impact": "May discover important information but could face dangers."
                    },
                    {
                        "option_id": "B",
                        "title": "Return to Base",
                        "description": "Return to base to resupply and report findings.",
                        "impact": "Ensures safety but might miss important opportunities."
                    },
                    {
                        "option_id": "C",
                        "title": "Seek Allies",
                        "description": "Contact nearby allies for assistance.",
                        "impact": "Increases chances of success but requires waiting time."
                    },
                    {
                        "option_id": "D",
                        "title": "Change Plans",
                        "description": "Try a new solution.",
                        "impact": "Could lead to unexpected breakthroughs."
                    }
                ]
            
        except Exception as e:
            logger.error(f"Error generating plot options: {str(e)}")
            raise

    async def generate_next_chapter(self, title: str, genre: str, outline: str, previous_chapter: str, chosen_option: dict, chapter_number: int) -> str:
        """Generate next chapter based on chosen option"""
        try:
            logger.info(f"Generating chapter {chapter_number} based on chosen option")
            
            prompt = f"""Please write chapter {chapter_number} for the novel "{title}" ({genre}).

            Previous Chapter Summary:
            {previous_chapter[:500]}...

            Reader's Chosen Plot Development:
            Title: {chosen_option['title']}
            Description: {chosen_option['description']}
            Impact: {chosen_option['impact']}
            Votes: {chosen_option['votes']} votes

            Overall Outline:
            {outline}

            Requirements:
            1. Word count: around 2000 words
            2. Naturally continue from previous chapter
            3. Reflect readers' chosen plot development
            4. Leave cliffhanger for next chapter
            5. Maintain character consistency
            6. Control story pacing
            7. Detailed scene and psychological descriptions
            8. Add appropriate dialogue and interactions
            """

            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a professional novelist specializing in creating engaging stories based on reader choices."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=3000
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"Error generating next chapter: {str(e)}")
            raise 