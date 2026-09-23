import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session

os.makedirs("data", exist_ok=True)
DATABASE_URL = "sqlite:///./data/yuri_ai.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

class Conversation(Base):
    __tablename__ = "conversations"
    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String(255), unique=True, index=True, nullable=False)
    title = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)

class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    role = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)
    conversation_id = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

class Memory(Base):
    __tablename__ = "memories"
    id = Column(Integer, primary_key=True, index=True)
    scope = Column(String(100), nullable=False)
    key = Column(String(255), nullable=False)
    value = Column(Text)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_project(db: Session, name: str, description: str = None):
    proj = Project(name=name, description=description)
    db.add(proj)
    db.commit()
    db.refresh(proj)
    return proj

def list_projects(db: Session):
    return db.query(Project).all()

def create_conversation(db: Session, external_id: str, project_id: int = None, title: str = None):
    conv = Conversation(external_id=external_id, title=title)
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv

def get_conversation_by_external_id(db: Session, external_id: str):
    return db.query(Conversation).filter(Conversation.external_id == external_id).first()

def list_conversations(db: Session):
    return db.query(Conversation).all()

def add_message(db: Session, conversation_id: int, role: str, content: str):
    msg = Message(conversation_id=conversation_id, role=role, content=content)
    db.add(msg)
    db.commit()
    return msg

def get_messages(db: Session, conversation_id: int):
    return db.query(Message).filter(Message.conversation_id == conversation_id).all()

def remember(db: Session, scope: str, key: str, value: str):
    from sqlalchemy import and_
    mem = db.query(Memory).filter(and_(Memory.scope == scope, Memory.key == key)).first()
    if mem:
        mem.value = value
    else:
        mem = Memory(scope=scope, key=key, value=value)
        db.add(mem)
    db.commit()

def recall(db: Session, scope: str, key: str):
    from sqlalchemy import and_
    mem = db.query(Memory).filter(and_(Memory.scope == scope, Memory.key == key)).first()
    return mem.value if mem else None

def list_memories(db: Session, scope: str = None):
    q = db.query(Memory)
    if scope:
        q = q.filter(Memory.scope == scope)
    return q.all()

def forget(db: Session, scope: str, key: str):
    from sqlalchemy import and_
    mem = db.query(Memory).filter(and_(Memory.scope == scope, Memory.key == key)).first()
    if mem:
        db.delete(mem)
        db.commit()
        return True
    return False
