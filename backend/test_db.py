from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
engine = create_engine('postgresql://foodweb_user:foodweb@localhost/foodweb')
Session = sessionmaker(bind=engine)
session = Session()
try:
    print('Users:', session.execute(text('SELECT count(*) FROM "user"')).scalar())
    print('Teams:', session.execute(text('SELECT count(*) FROM team')).scalar())
    print('Joins:', session.execute(text('SELECT count(*) FROM jointeam')).scalar())
except Exception as e:
    print(e)
