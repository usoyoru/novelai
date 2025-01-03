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

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from bot.app.models.novel import Novel, Chapter, PlotOption, Vote
from bot.app.database import SessionLocal, engine, Base, init_db

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 初始化数据库
init_db()
logger.info("数据库初始化完成")

app = FastAPI(title="Novel Website")

# 挂载静态文件
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# 设置模板
templates = Jinja2Templates(directory="app/templates")

# 依赖项
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
async def home(request: Request, db: Session = Depends(get_db)):
    """首页，显示所有小说列表"""
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
    """小说详情页，显示所有章节"""
    try:
        novel = db.query(Novel).filter(Novel.id == novel_id).first()
        if not novel:
            raise HTTPException(status_code=404, detail="小说未找到")
            
        chapters = db.query(Chapter).filter(
            Chapter.novel_id == novel_id
        ).order_by(Chapter.chapter_number).all()
        
        # 获取最新章节的投票选项
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
    """章节详情页"""
    try:
        chapter = db.query(Chapter).filter(
            Chapter.novel_id == novel_id,
            Chapter.chapter_number == chapter_number
        ).first()
        
        if not chapter:
            raise HTTPException(status_code=404, detail="章节未找到")
            
        novel = db.query(Novel).filter(Novel.id == novel_id).first()
        if not novel:
            raise HTTPException(status_code=404, detail="小说未找到")
        
        # 获取本章的投票选项
        plot_options = db.query(PlotOption).filter(
            PlotOption.novel_id == novel_id,
            PlotOption.chapter_number == chapter_number
        ).order_by(PlotOption.created_at.desc()).limit(4).all()  # 只获取最新的4个选项
        
        # 如果有选项，确保它们是同一批次的（创建时间相同）
        if plot_options:
            latest_created_at = plot_options[0].created_at
            plot_options = [opt for opt in plot_options if opt.created_at == latest_created_at]
        
        if not plot_options:
            raise HTTPException(status_code=404, detail="投票选项未找到")
        
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
    """投票页面"""
    try:
        novel = db.query(Novel).filter(Novel.id == novel_id).first()
        if not novel:
            raise HTTPException(status_code=404, detail="小说未找到")
            
        plot_options = db.query(PlotOption).filter(
            PlotOption.novel_id == novel_id,
            PlotOption.chapter_number == chapter_number
        ).all()
        
        if not plot_options:
            raise HTTPException(status_code=404, detail="投票选项未找到")
            
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
    """提交投票"""
    try:
        # 验证钱包地址格式
        try:
            public_key = Pubkey.from_string(wallet_address)
        except ValueError:
            raise HTTPException(status_code=400, detail="无效的钱包地址")
            
        # 验证签名
        try:
            message = f"Vote for chapter {chapter_number}"
            message_bytes = message.encode('utf-8')
            signature_bytes = bytes.fromhex(signature)
            
            # 使用公钥验证签名
            verify_key = nacl.signing.VerifyKey(bytes(public_key))
            verify_key.verify(message_bytes, signature_bytes)
        except Exception as e:
            logger.error(f"签名验证失败: {str(e)}")
            raise HTTPException(status_code=400, detail="签名验证失败")
        
        # 检查是否已经投过票
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
            raise HTTPException(status_code=400, detail="您已经投过票了")
            
        # 获取投票选项
        plot_option = db.query(PlotOption).filter(
            PlotOption.id == option_id,
            PlotOption.novel_id == novel_id,
            PlotOption.chapter_number == chapter_number
        ).first()
        
        if not plot_option:
            raise HTTPException(status_code=404, detail="投票选项未找到")
            
        # 确保选项是最新的一批
        latest_options = db.query(PlotOption).filter(
            PlotOption.novel_id == novel_id,
            PlotOption.chapter_number == chapter_number
        ).order_by(PlotOption.created_at.desc()).limit(4).all()
        
        if latest_options:
            latest_created_at = latest_options[0].created_at
            if plot_option.created_at != latest_created_at:
                raise HTTPException(status_code=400, detail="投票选项已过期")
        
        try:
            # 创建投票记录
            vote = Vote(
                plot_option_id=plot_option.id,
                wallet_address=str(public_key)
            )
            db.add(vote)
            
            # 更新票数
            plot_option.votes_count += 1
            
            # 提交事务
            db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"Error saving vote: {str(e)}")
            raise HTTPException(status_code=500, detail="保存投票失败")
        
        # 重定向回投票页面
        return Response(
            status_code=303,
            headers={"Location": f"/vote/{novel_id}/{chapter_number}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in submit_vote route: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 