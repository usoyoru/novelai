# AI Interactive Novel

An interactive web application that generates stories using GPT-3.5 and allows users to vote on the story's direction. The story updates every 10 minutes based on user votes.

## Features

- AI-powered story generation using GPT-3.5
- Interactive voting system for story direction
- Real-time vote counting
- Automatic story updates every 10 minutes
- Multiple concurrent stories support
- Solana wallet integration for voting
- Mobile-friendly responsive design

## Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/novelai.git
cd novelai
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the root directory:
```bash
cp .env.example .env
```

4. Edit `.env` and add your OpenAI API key:
```
OPENAI_API_KEY=your_api_key_here
```

## Usage

1. Run the web application:
```bash
python app.py
```

2. Create new stories (admin only):
```bash
python create_story.py
```

3. Clean database (admin only):
```bash
python clean_database.py
```

## Development

- `app.py`: Main web application
- `create_story.py`: Script for creating new stories
- `clean_database.py`: Script for cleaning the database
- `templates/`: HTML templates
- `static/`: Static files (CSS, JS, etc.)

## Security

- The `.env` file containing sensitive information is not tracked by git
- Make sure to never commit API keys or sensitive data
- Use the provided `.env.example` as a template

## License

MIT License 