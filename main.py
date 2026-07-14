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


# uvicorn main:app --reload -> pornire server API
# http://127.0.0.1:8000/docs -> link interfata Swagger UI pentru testare API