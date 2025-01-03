from fastapi import FastAPI, Request, Depends, HTTPException, Response, Form
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import func
import sys
import os
from datetime import datetime, timedelta, timezone
import base58
from solana.publickey import PublicKey
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
    """Novel detail page, displays all chapters"""
    try:
        novel = db.query(Novel).filter(Novel.id == novel_id).first()
        if not novel:
            raise HTTPException(status_code=404, detail="Novel not found")
            
        chapters = db.query(Chapter).filter(
            Chapter.novel_id == novel_id
        ).order_by(Chapter.chapter_number).all()
        
        # Get voting options for the latest chapter
        latest_options = db.query(PlotOption).filter(
            PlotOption.novel_id == novel_id,
            PlotOption.chapter_number == novel.current_chapter
        ).all()
        
        return templates.TemplateResponse(
            "novel.html",
            {
                "request": request,
                "novel": novel,
                "chapters": chapters,
                "latest_options": latest_options
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
        chapter = db.query(Chapter).filter(
            Chapter.novel_id == novel_id,
            Chapter.chapter_number == chapter_number
        ).first()
        
        if not chapter:
            raise HTTPException(status_code=404, detail="Chapter not found")
            
        novel = db.query(Novel).filter(Novel.id == novel_id).first()
        if not novel:
            raise HTTPException(status_code=404, detail="Novel not found")
        
        # Get voting options for this chapter
        plot_options = db.query(PlotOption).filter(
            PlotOption.novel_id == novel_id,
            PlotOption.chapter_number == chapter_number
        ).order_by(PlotOption.created_at.desc()).limit(4).all()  # Only get latest 4 options
        
        # If there are options, ensure they are from the same batch (same creation time)
        if plot_options:
            latest_created_at = plot_options[0].created_at
            plot_options = [opt for opt in plot_options if opt.created_at == latest_created_at]
        
        if not plot_options:
            raise HTTPException(status_code=404, detail="Voting options not found")
        
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

@app.get("/vote/{novel_id}/{chapter_number}")
async def vote_page(
    request: Request,
    novel_id: int,
    chapter_number: int,
    db: Session = Depends(get_db)
):
    """Vote page"""
    try:
        novel = db.query(Novel).filter(Novel.id == novel_id).first()
        if not novel:
            raise HTTPException(status_code=404, detail="Novel not found")
            
        plot_options = db.query(PlotOption).filter(
            PlotOption.novel_id == novel_id,
            PlotOption.chapter_number == chapter_number
        ).all()
        
        if not plot_options:
            raise HTTPException(status_code=404, detail="Voting options not found")
            
        return templates.TemplateResponse(
            "vote.html",
            {
                "request": request,
                "novel": novel,
                "chapter_number": chapter_number,
                "plot_options": plot_options
            }
        )
    except Exception as e:
        logger.error(f"Error in vote_page route: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/vote/{novel_id}/{chapter_number}/{option_id}")
async def submit_vote(
    request: Request,
    novel_id: int,
    chapter_number: int,
    option_id: int,
    wallet_address: str = Form(...),
    signature: str = Form(...),
    db: Session = Depends(get_db)
):
    """Submit vote"""
    try:
        # Validate wallet address format
        try:
            public_key = PublicKey(wallet_address)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid wallet address")
            
        # Verify signature
        try:
            message = f"Vote for chapter {chapter_number}"
            message_bytes = message.encode('utf-8')
            signature_bytes = bytes.fromhex(signature)
            
            # Verify signature using public key
            verify_key = nacl.signing.VerifyKey(bytes(public_key))
            verify_key.verify(message_bytes, signature_bytes)
        except Exception as e:
            logger.error(f"Signature verification failed: {str(e)}")
            raise HTTPException(status_code=400, detail="Signature verification failed")
        
        # Check if already voted
        existing_vote = db.query(Vote).join(PlotOption).filter(
            PlotOption.novel_id == novel_id,
            PlotOption.chapter_number == chapter_number,
            Vote.wallet_address == str(public_key),
            PlotOption.created_at == db.query(PlotOption.created_at)
                .filter(PlotOption.novel_id == novel_id)
                .filter(PlotOption.chapter_number == chapter_number)
                .order_by(PlotOption.created_at.desc())
                .limit(1)
                .scalar_subquery()
        ).first()
        
        if existing_vote:
            raise HTTPException(status_code=400, detail="You have already voted")
            
        # Get voting option
        plot_option = db.query(PlotOption).filter(
            PlotOption.id == option_id,
            PlotOption.novel_id == novel_id,
            PlotOption.chapter_number == chapter_number
        ).first()
        
        if not plot_option:
            raise HTTPException(status_code=404, detail="Voting option not found")
            
        # Ensure the option is from the latest batch
        latest_options = db.query(PlotOption).filter(
            PlotOption.novel_id == novel_id,
            PlotOption.chapter_number == chapter_number
        ).order_by(PlotOption.created_at.desc()).limit(4).all()
        
        if latest_options:
            latest_created_at = latest_options[0].created_at
            if plot_option.created_at != latest_created_at:
                raise HTTPException(status_code=400, detail="Voting option has expired")
        
        try:
            # Create vote record
            vote = Vote(
                plot_option_id=plot_option.id,
                wallet_address=str(public_key)
            )
            db.add(vote)
            
            # Update vote count
            plot_option.votes_count += 1
            
            # Commit transaction
            db.commit()
            
            return {"detail": "Vote successful"}
            
        except Exception as e:
            db.rollback()
            logger.error(f"Database error: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to save vote")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in submit_vote route: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 