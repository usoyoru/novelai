import os
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from apscheduler.schedulers.background import BackgroundScheduler
import openai
from dotenv import load_dotenv
from markupsafe import Markup
import requests
import time
import threading

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL')
if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL or 'sqlite:///stories.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Constants
TOKEN_ADDRESS = "XXXXXX"
SOLANA_RPC_URL = "https://api.mainnet-beta.solana.com"


processing_lock = threading.Lock()
processed_stories = set()

def check_token_balance(wallet_address):
    """Check if the wallet holds the required token"""
    try:
        
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getTokenAccountsByOwner",
            "params": [
                wallet_address,
                {
                    "mint": TOKEN_ADDRESS
                },
                {
                    "encoding": "jsonParsed"
                }
            ]
        }
        
        response = requests.post(SOLANA_RPC_URL, json=payload)
        data = response.json()
        
        if "result" in data and "value" in data["result"]:
            for token_account in data["result"]["value"]:
                if "account" in token_account and "data" in token_account["account"]:
                    parsed_data = token_account["account"]["data"]["parsed"]
                    if "info" in parsed_data and "tokenAmount" in parsed_data["info"]:
                        amount = float(parsed_data["info"]["tokenAmount"]["uiAmount"])
                        if amount > 0:
                            return True
        return False
    except Exception as e:
        print(f"Error checking token balance: {e}")
        return False

def get_wallet_token_balance(wallet_address):
    """Get token balance for a specific wallet"""
    try:
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getTokenAccountsByOwner",
            "params": [
                wallet_address,
                {
                    "mint": TOKEN_ADDRESS
                },
                {
                    "encoding": "jsonParsed"
                }
            ]
        }
        
        response = requests.post(SOLANA_RPC_URL, json=payload)
        data = response.json()
        
        if "result" in data and "value" in data["result"]:
            for token_account in data["result"]["value"]:
                if "account" in token_account and "data" in token_account["account"]:
                    parsed_data = token_account["account"]["data"]["parsed"]
                    if "info" in parsed_data and "tokenAmount" in parsed_data["info"]:
                        return float(parsed_data["info"]["tokenAmount"]["uiAmount"])
        return 0
    except Exception as e:
        print(f"Error getting token balance: {e}")
        return 0

# Add nl2br filter
@app.template_filter('nl2br')
def nl2br(value):
    """Convert newlines to <br> tags."""
    if not value:
        return ''
    return Markup(value.replace('\n', '<br>\n'))

# Initialize OpenAI API
openai.api_key = os.getenv('OPENAI_API_KEY')

# Database Models
class Story(db.Model):
    """Story model to store the generated story chapters"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    current_chapter = db.Column(db.Integer, default=1)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    next_update = db.Column(db.DateTime, default=lambda: datetime.utcnow() + timedelta(minutes=10))

class Option(db.Model):
    """Options model to store voting options for the next chapter"""
    id = db.Column(db.Integer, primary_key=True)
    story_id = db.Column(db.Integer, db.ForeignKey('story.id'), nullable=False)
    description = db.Column(db.Text, nullable=False)
    votes = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Vote(db.Model):
    """Vote model to store voting records"""
    id = db.Column(db.Integer, primary_key=True)
    story_id = db.Column(db.Integer, db.ForeignKey('story.id'), nullable=False)
    option_id = db.Column(db.Integer, db.ForeignKey('option.id'), nullable=False)
    wallet_address = db.Column(db.String(44), nullable=False)
    signature = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ProcessLock(db.Model):
    """Process lock model to prevent multiple processes from processing the same story"""
    id = db.Column(db.Integer, primary_key=True)
    story_id = db.Column(db.Integer, unique=True, nullable=False)
    locked_at = db.Column(db.DateTime, default=datetime.utcnow)

def generate_chapter(prompt):
    """Generate a new chapter using GPT"""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a creative story writer. Write an engaging chapter for a novel."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error generating chapter: {e}")
        return None

def generate_options(chapter_content):
    """Generate voting options for the next chapter"""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a creative story writer. Please generate 4 different story development options. Each option should be concise but engaging, providing a unique direction for the story."},
                {"role": "user", "content": f"Based on this chapter content: {chapter_content}\nPlease generate 4 different story development options. Number each option (1-4) and ensure clear distinctions between options."}
            ],
            max_tokens=800,
            temperature=0.8
        )
        
        content = response.choices[0].message.content
        options = []
        
        lines = content.split('\n')
        current_option = ""
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if (line.startswith('1.') or line.startswith('2.') or 
                line.startswith('3.') or line.startswith('4.') or
                line.startswith('1)') or line.startswith('2)') or
                line.startswith('3)') or line.startswith('4)')):
                
                if current_option:
                    options.append(current_option.strip())
                current_option = line.split('.', 1)[-1].split(')', 1)[-1].strip()
            else:
                if current_option:
                    current_option += " " + line
        
        if current_option:
            options.append(current_option.strip())
        
        options = options[:4]
        while len(options) < 4:
            options.append(f"Explore direction {len(options) + 1} of the story")
        
        final_options = []
        for i, opt in enumerate(options, 1):
            if not opt or len(opt.strip()) < 5:
                final_options.append(f"Option {i}: Explore a new direction in the story")
            else:
                final_options.append(opt)
        
        return final_options
        
    except Exception as e:
        print(f"Error generating options: {e}")
        
        return [
            "Lead the protagonist on an exciting adventure",
            "Explore an unexpected twist",
            "Introduce a mysterious new character",
            "Reveal an important secret"
        ]

def process_votes():
    """Process votes and generate new chapter based on winning option"""
    print("Starting vote processing...")
    
    with app.app_context():
        try:
            current_time = datetime.utcnow()
            stories = Story.query.filter(Story.next_update <= current_time).all()
            print(f"Found {len(stories)} stories to update")
            
            for story in stories:
                try:
                    lock = ProcessLock(story_id=story.id)
                    db.session.add(lock)
                    db.session.commit()
                except Exception as e:
                    print(f"Story {story.id} is being processed by another worker, skipping...")
                    db.session.rollback()
                    continue
                
                try:
                    print(f"Processing story {story.id}")
                    options = Option.query.filter_by(story_id=story.id).all()
                    if options:
                        winning_option = max(options, key=lambda x: x.votes)
                        print(f"Winning option: {winning_option.description} with {winning_option.votes} votes")
                        
                        prompt = f"""Continue the story based on this choice: {winning_option.description}

Previous chapter content:
{story.content.split('Chapter')[-1]}

Write the next chapter that follows this choice. Make it engaging and consistent with the story's style."""
                        
                        new_chapter = generate_chapter(prompt)
                        if new_chapter:
                            print("Successfully generated new chapter")
                            
                            new_story = Story(
                                title=story.title,
                                content=f"Chapter {story.current_chapter + 1}:\n{new_chapter}",
                                current_chapter=story.current_chapter + 1,
                                next_update=current_time + timedelta(minutes=10)
                            )
                            db.session.add(new_story)
                            db.session.flush()
                            
                            print("Deleting votes...")
                            Vote.query.filter_by(story_id=story.id).delete()
                            
                            print("Deleting old options...")
                            Option.query.filter_by(story_id=story.id).delete()
                            
                            print("Generating new options...")
                            new_options = generate_options(new_chapter)
                            for opt in new_options:
                                new_option = Option(story_id=new_story.id, description=opt)
                                db.session.add(new_option)
                            
                            db.session.commit()
                            print("Successfully created new story and options")
                        else:
                            print("Failed to generate new chapter")
                    else:
                        print(f"No options found for story {story.id}")
                finally:
                    try:
                        ProcessLock.query.filter_by(story_id=story.id).delete()
                        db.session.commit()
                    except:
                        db.session.rollback()
                
        except Exception as e:
            print(f"Error in process_votes: {str(e)}")
            db.session.rollback()

def get_token_info():
    """Get token supply and holder count"""
    try:
        
        supply_payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getTokenSupply",
            "params": [TOKEN_ADDRESS]
        }
        
        supply_response = requests.post(SOLANA_RPC_URL, json=supply_payload)
        supply_data = supply_response.json()
        
        
        accounts_payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getProgramAccounts",
            "params": [
                "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA",
                {
                    "filters": [
                        {
                            "dataSize": 165
                        },
                        {
                            "memcmp": {
                                "offset": 0,
                                "bytes": TOKEN_ADDRESS
                            }
                        }
                    ],
                    "encoding": "jsonParsed"
                }
            ]
        }
        
        accounts_response = requests.post(SOLANA_RPC_URL, json=accounts_payload)
        accounts_data = accounts_response.json()
        
        total_supply = 0
        holder_count = 0
        
        if "result" in supply_data and "value" in supply_data["result"]:
            total_supply = float(supply_data["result"]["value"]["uiAmount"])
        
        if "result" in accounts_data:
            holder_count = len([acc for acc in accounts_data["result"] if acc["account"]["data"]["parsed"]["info"]["tokenAmount"]["uiAmount"] > 0])
        
        return {
            "total_supply": total_supply,
            "holder_count": holder_count,
            "token_address": TOKEN_ADDRESS
        }
    except Exception as e:
        print(f"Error getting token info: {e}")
        return {
            "total_supply": 0,
            "holder_count": 0,
            "token_address": TOKEN_ADDRESS
        }

@app.route('/token_info')
def token_info():
    """Get token information"""
    return jsonify(get_token_info())

@app.route('/wallet_balance/<wallet_address>')
def wallet_balance(wallet_address):
    """Get wallet token balance"""
    balance = get_wallet_token_balance(wallet_address)
    return jsonify({
        "balance": balance,
        "token_address": TOKEN_ADDRESS
    })

# Initialize scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(process_votes, 'interval', minutes=1)
scheduler.start()

# Create database tables
def init_db():
    """Initialize database with retry mechanism"""
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            with app.app_context():
                
                try:
                    Vote.query.delete()
                    Option.query.delete()
                    Story.query.delete()
                    db.session.commit()
                except:
                    db.session.rollback()
                
                
                db.drop_all()
                
                db.create_all()
                print("Database tables created successfully!")
                return True
        except Exception as e:
            print(f"Error initializing database (attempt {retry_count + 1}/{max_retries}): {str(e)}")
            retry_count += 1
            if retry_count < max_retries:
                print("Retrying...")
                time.sleep(2)  
    
    print("Failed to initialize database after multiple attempts")
    return False

# Initialize database
init_db()

@app.route('/')
def index():
    """Home page route"""
    stories = Story.query.all()
    token_data = get_token_info()
    return render_template('index.html', stories=stories, token_data=token_data)

@app.route('/vote', methods=['POST'])
def vote():
    """Handle voting for story options"""
    try:
        option_id = request.form.get('option_id')
        wallet_address = request.form.get('wallet_address')
        signature = request.form.get('signature')
        
        if not all([option_id, wallet_address, signature]):
            return jsonify({'error': 'Missing required parameters'}), 400
        
        
        if not check_token_balance(wallet_address):
            return jsonify({'error': 'You need to hold the required token to vote'}), 403
        
        option = Option.query.get(option_id)
        if not option:
            return jsonify({'error': 'Option not found'}), 404
        
        # Verify the wallet hasn't voted for this story yet
        existing_votes = Vote.query.filter_by(
            story_id=option.story_id,
            wallet_address=wallet_address
        ).first()
        
        if existing_votes:
            return jsonify({'error': 'You have already voted for this chapter'}), 400
        
        # Record the vote
        vote = Vote(
            story_id=option.story_id,
            option_id=option.id,
            wallet_address=wallet_address,
            signature=signature
        )
        db.session.add(vote)
        
        # Increment vote count
        option.votes += 1
        db.session.commit()
        
        return jsonify({'success': True, 'votes': option.votes})
    except Exception as e:
        print(f"Error processing vote: {str(e)}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/story/<int:story_id>')
def view_story(story_id):
    """View a specific story"""
    story = Story.query.get_or_404(story_id)
    options = Option.query.filter_by(story_id=story_id).all()
    return render_template('story.html', story=story, options=options)

if __name__ == '__main__':
    app.run(debug=True) 