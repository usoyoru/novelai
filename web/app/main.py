from fastapi import FastAPI, Request, Depends, HTTPException, Response, Form
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import func
import sys
import os
from datetime import datetime, timedelta, timezone
import base58
from solders.pubkey import Pubkey
import nacl.signing
import nacl.encoding
import logging

# Add project root directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from bot.app.models.novel import Novel, Chapter, PlotOption, Vote
from bot.app.database import SessionLocal, engine, Base, init_db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize database
init_db()
logger.info("Database initialization completed")

app = FastAPI(title="Novel Website")

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Set up templates
templates = Jinja2Templates(directory="app/templates")

# Dependencies
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
async def home(request: Request, db: Session = Depends(get_db)):
    """Home page, displays all novels"""
    try:
        novels = db.query(Novel).order_by(Novel.created_at.desc()).all()
        return templates.TemplateResponse(
            "index.html",
            {"request": request, "novels": novels}
        )
    except Exception as e:
        logger.error(f"Error in home route: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/novel/{novel_id}")
async def novel_detail(request: Request, novel_id: int, db: Session = Depends(get_db)):
    """Novel detail page"""
    try:
        novel = db.query(Novel).filter(Novel.id == novel_id).first()
        if not novel:
            raise HTTPException(status_code=404, detail="Novel not found")
            
        chapters = db.query(Chapter).filter(Chapter.novel_id == novel_id).order_by(Chapter.chapter_number).all()
        
        return templates.TemplateResponse(
            "novel.html",
            {
                "request": request,
                "novel": novel,
                "chapters": chapters
            }
        )
    except Exception as e:
        logger.error(f"Error in novel_detail route: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/chapter/{novel_id}/{chapter_number}")
async def chapter_detail(
    request: Request,
    novel_id: int,
    chapter_number: int,
    db: Session = Depends(get_db)
):
    """Chapter detail page"""
    try:
        # Get novel
        novel = db.query(Novel).filter(Novel.id == novel_id).first()
        if not novel:
            raise HTTPException(status_code=404, detail="Novel not found")
            
        # Get chapter
        chapter = db.query(Chapter).filter(
            Chapter.novel_id == novel_id,
            Chapter.chapter_number == chapter_number
        ).first()
        
        if not chapter:
            raise HTTPException(status_code=404, detail="Chapter not found")
            
        # Get plot options
        plot_options = db.query(PlotOption).filter(
            PlotOption.novel_id == novel_id,
            PlotOption.chapter_number == chapter_number
        ).all()
        
        return templates.TemplateResponse(
            "chapter.html",
            {
                "request": request,
                "novel": novel,
                "chapter": chapter,
                "plot_options": plot_options
            }
        )
    except Exception as e:
        logger.error(f"Error in chapter_detail route: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/vote/{novel_id}/{chapter_number}/{option_id}")
async def vote_page(
    request: Request,
    novel_id: int,
    chapter_number: int,
    option_id: str,
    db: Session = Depends(get_db)
):
    """Vote page"""
    try:
        plot_option = db.query(PlotOption).filter(
            PlotOption.novel_id == novel_id,
            PlotOption.chapter_number == chapter_number,
            PlotOption.option_id == option_id
        ).first()
        
        if not plot_option:
            raise HTTPException(status_code=404, detail="Voting option not found")
            
        return templates.TemplateResponse(
            "vote.html",
            {
                "request": request,
                "plot_option": plot_option
            }
        )
    except Exception as e:
        logger.error(f"Error in vote_page route: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/submit_vote/{novel_id}/{chapter_number}/{option_id}")
async def submit_vote(
    novel_id: int,
    chapter_number: int,
    option_id: str,
    wallet_address: str = Form(...),
    signature: str = Form(...),
    db: Session = Depends(get_db)
):
    """Submit vote"""
    try:
        # Validate wallet address format
        try:
            public_key = Pubkey(wallet_address)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid wallet address")
            
        # Verify signature
        try:
            # Check if already voted
            existing_vote = db.query(Vote).join(PlotOption).filter(
                PlotOption.novel_id == novel_id,
                PlotOption.chapter_number == chapter_number,
                Vote.wallet_address == wallet_address
            ).first()
            
            if existing_vote:
                raise HTTPException(status_code=400, detail="You have already voted for this chapter")
            
            # Get plot option
            plot_option = db.query(PlotOption).filter(
                PlotOption.novel_id == novel_id,
                PlotOption.chapter_number == chapter_number,
                PlotOption.option_id == option_id
            ).first()
            
            if not plot_option:
                raise HTTPException(status_code=404, detail="Voting option not found")
            
            # Create vote record
            vote = Vote(
                plot_option_id=plot_option.id,
                wallet_address=wallet_address
            )
            db.add(vote)
            
            # Update vote count
            plot_option.votes_count = plot_option.votes_count + 1
            
            db.commit()
            
            return {"status": "success"}
            
        except Exception as e:
            logger.error(f"Error verifying signature: {str(e)}")
            raise HTTPException(status_code=400, detail="Invalid signature")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in submit_vote route: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/check_vote/{novel_id}/{chapter_number}")
async def check_vote(
    novel_id: int,
    chapter_number: int,
    wallet_address: str,
    db: Session = Depends(get_db)
):
    """Check if wallet has voted"""
    try:
        # Validate wallet address format
        try:
            public_key = Pubkey(wallet_address)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid wallet address")
            
        # Check if voted
        vote = db.query(Vote).join(PlotOption).filter(
            PlotOption.novel_id == novel_id,
            PlotOption.chapter_number == chapter_number,
            Vote.wallet_address == wallet_address
        ).first()
        
        return {"has_voted": vote is not None}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in check_vote route: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 