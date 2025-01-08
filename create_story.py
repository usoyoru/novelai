import os
from datetime import datetime
from dotenv import load_dotenv
import openai
from app import app, db, Story, Option, generate_chapter, generate_options

# Load environment variables
load_dotenv()

def create_story(title, prompt):
    """
    Create a new story with the given title and prompt.
    
    Args:
        title (str): The title of the story
        prompt (str): The prompt to generate the first chapter
    
    Returns:
        Story: The created story object
    """
    with app.app_context():
        # Check if story with same title exists
        existing_story = Story.query.filter_by(title=title).first()
        if existing_story:
            print(f"Error: Story with title '{title}' already exists")
            return None

        # Generate first chapter
        print(f"Generating first chapter for '{title}'...")
        first_chapter = generate_chapter(prompt)
        if not first_chapter:
            print("Failed to generate story")
            return None
        
        # Create story
        story = Story(
            title=title,
            content=f"Chapter 1:\n{first_chapter}"
        )
        db.session.add(story)
        db.session.commit()
        print(f"Created story with ID: {story.id}")
        
        # Generate options
        print("Generating voting options...")
        options = generate_options(first_chapter)
        for opt in options:
            option = Option(story_id=story.id, description=opt)
            db.session.add(option)
        db.session.commit()
        print("Created voting options")
        
        print(f"\nStory content:")
        print("-" * 50)
        print(story.content)
        print("-" * 50)
        print("\nVoting options:")
        for i, opt in enumerate(options, 1):
            print(f"{i}. {opt}")
        
        return story

if __name__ == "__main__":
    # Example stories to create
    stories = [
        {
            "title": "The Crypto Rebellion",
            "prompt": """Write the first chapter of a story about a young Wall Street trader who discovers a revolutionary cryptocurrency project that could challenge the entire financial system.

The story should include:
- A protagonist who is a disillusioned Wall Street trader in New York, who used to work at Goldman Sachs
- A mysterious Layer 1 blockchain technology that promises zero gas fees and instant finality
- A secret group of crypto developers who have been working underground for years
- Elements of corporate espionage from competing blockchain projects
- SEC investigation and government surveillance
- A mentor figure who is a legendary early Bitcoin investor (turned billionaire) from the 2011 era
- High-stakes financial drama involving billion-dollar crypto funds
- A potential conspiracy involving stablecoin manipulation
- References to real crypto history like Mt.Gox hack and Silk Road

Style: Write in an American thriller style, similar to Michael Lewis or Robert Harris, with fast-paced narrative and technical details woven naturally into the story. Include realistic crypto trading scenes and blockchain technical discussions."""
        }
    ]
    
    print("AI Interactive Novel - Story Creator")
    print("=" * 40)
    
    # Let user choose to create example stories or input custom story
    choice = input("\nDo you want to:\n1. Create the crypto story\n2. Create custom story\nEnter choice (1 or 2): ")
    
    if choice == "1":
        story_data = stories[0]
        print(f"\nCreating story: {story_data['title']}")
        create_story(story_data["title"], story_data["prompt"])
    
    elif choice == "2":
        title = input("\nEnter story title: ")
        print("\nEnter story prompt (press Enter twice to finish):")
        prompt_lines = []
        while True:
            line = input()
            if not line and prompt_lines:
                break
            prompt_lines.append(line)
        prompt = "\n".join(prompt_lines)
        
        if title and prompt:
            create_story(title, prompt)
        else:
            print("Error: Title and prompt are required")
    
    else:
        print("Invalid choice") 