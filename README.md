# AI Interactive Novel

An AI-powered interactive novel platform where readers can vote to determine the story's direction.

## Heroku Deployment Steps

1. Install Heroku CLI and login:
```bash
heroku login
```

2. Create Heroku app:
```bash
heroku create your-app-name
```

3. Add PostgreSQL database:
```bash
heroku addons:create heroku-postgresql:mini
```

4. Set environment variables:
```bash
heroku config:set OPENAI_API_KEY=your_openai_api_key
```

5. Deploy code:
```bash
git push heroku main
```

6. Start worker process:
```bash
heroku ps:scale worker=1
```

## Remote Management Commands

1. Clean database:
```bash
heroku run python manage.py clean
```

2. Start bot:
```bash
heroku run python manage.py start
```

3. Stop bot:
```bash
heroku ps:stop worker.1
```

## Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set environment variables:
```bash
cp .env.example .env
# Edit .env file and fill in required configurations
```

3. Run website:
```bash
cd web && uvicorn app.main:app --reload
```

4. Run bot:
```bash
python manage.py start
``` 