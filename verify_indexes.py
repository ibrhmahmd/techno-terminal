import os
from dotenv import load_dotenv
load_dotenv()
from sqlalchemy import create_engine, text

url = os.environ.get('DATABASE_URL')
engine = create_engine(url)
with engine.connect() as conn:
    result = conn.execute(text("""
        SELECT indexname, tablename FROM pg_indexes 
        WHERE tablename IN ('teams', 'team_members') 
        AND indexname LIKE 'idx_%%'
        ORDER BY tablename, indexname
    """))
    for row in result:
        print(f'{row[1]}.{row[0]}')
