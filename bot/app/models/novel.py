from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, JSON, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base

class Novel(Base):
    """Novel model for storing story information"""
    __tablename__ = "novels"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    genre = Column(String)
    outline = Column(Text)
    current_chapter = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    chapters = relationship("Chapter", back_populates="novel")
    plot_options = relationship("PlotOption", back_populates="novel")

class Chapter(Base):
    """Chapter model for storing novel chapters"""
    __tablename__ = "chapters"

    id = Column(Integer, primary_key=True, index=True)
    novel_id = Column(Integer, ForeignKey("novels.id"))
    chapter_number = Column(Integer)
    content = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    tweet_id = Column(String)  # Store the ID of the tweet when published to Twitter

    novel = relationship("Novel", back_populates="chapters")

class PlotOption(Base):
    """Plot option model for storing voting options"""
    __tablename__ = "plot_options"

    id = Column(Integer, primary_key=True, index=True)
    novel_id = Column(Integer, ForeignKey("novels.id"))
    chapter_number = Column(Integer)  # Associated chapter number
    option_id = Column(String)  # A, B, C, D
    title = Column(String)
    description = Column(Text)
    impact = Column(Text)
    votes_count = Column(Integer, default=0)  # Total votes
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_winner = Column(Boolean, default=False)

    novel = relationship("Novel", back_populates="plot_options")
    votes = relationship("Vote", back_populates="plot_option")

class Vote(Base):
    """Vote model for storing user votes"""
    __tablename__ = "votes"

    id = Column(Integer, primary_key=True, index=True)
    plot_option_id = Column(Integer, ForeignKey("plot_options.id"))
    wallet_address = Column(String)  # Store voting wallet address
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    plot_option = relationship("PlotOption", back_populates="votes") 