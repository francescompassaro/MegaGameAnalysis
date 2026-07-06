# database.py
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Date
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = "sqlite:///./pauper_lega.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Modelli del Database
class Giocatore(Base):
    __tablename__ = 'giocatori'
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, unique=True, nullable=False)
    mazzo_predefinito = Column(String)

# --- QUESTO ERA IL MODELLO MANCANTE ---
class Tappa(Base):
    __tablename__ = 'tappe'
    id = Column(Integer, primary_key=True, index=True)
    numero_tappa = Column(Integer, nullable=False)
    data = Column(String, nullable=True) # Puoi usare String o Date per la data della tappa

class Match(Base):
    __tablename__ = 'matchs'
    id = Column(Integer, primary_key=True, index=True)
    tappa_id = Column(Integer, ForeignKey('tappe.id')) # Legato alla tabella tappe
    g1_id = Column(Integer, ForeignKey('giocatori.id'))
    g2_id = Column(Integer, ForeignKey('giocatori.id'), nullable=True) # Null se è un BYE
    vittorie_g1 = Column(Integer, default=0)
    vittorie_g2 = Column(Integer, default=0)
    pareggi = Column(Integer, default=0)

# Crea le tabelle nel file .db se non esistono
Base.metadata.create_all(bind=engine)

# Dipendenza per FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()