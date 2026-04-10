from app.database import Base, engine

# Import ALL models so SQLAlchemy knows them
from models.users import User
from models.wallet import Wallet
from models.ledger import Ledger


Base.metadata.create_all(bind=engine)

print("Tables created successfully!")