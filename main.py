from fastapi import FastAPI
import mysql.connector

app = FastAPI()

def get_db_connection():
    return mysql.connector.connect(host='localhost', user='admin', password='admin', database='news_db')

@app.get("/news")
async def get_news():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM articles ORDER BY publishedAt DESC")
    articles = cursor.fetchall()
    conn.close()
    return articles

@app.get("/news/{article_id}")
async def get_news_article(article_id: int):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM articles WHERE id = %s", (article_id,))
    article = cursor.fetchone()
    conn.close()
    return article

@app.get("/news/author/{author_name}")
async def get_news_by_author(author_name: str):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM articles WHERE author = %s ORDER BY publishedAt DESC", (author_name,))
    articles = cursor.fetchall()
    conn.close()
    return articles

@app.get("/news/source/{source_name}")
async def get_news_by_source(source_name: str):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM articles WHERE source = %s ORDER BY publishedAt DESC", (source_name,))
    articles = cursor.fetchall()
    conn.close()
    return articles

# uvicorn main:app --reload -> pornire server API
# http://127.0.0.1:8000/docs -> link interfata Swagger UI pentru testare API