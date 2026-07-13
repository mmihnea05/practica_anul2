import requests
from bs4 import BeautifulSoup
import mysql.connector
import ollama
from datetime import datetime

def generate_summary(text):
    try:
        response = ollama.chat(model='llama3.2', messages=[
            {'role': 'user', 'content': f'Genereaza o descriere scurta (max 200 caractere) pentru: {text[:1000]}'}
        ])
        return response['message']['content']
    except Exception:
        return text[:197] + "..."

def save_to_db(data):
    conn = mysql.connector.connect(host='localhost', user='admin', password='admin', database='news_db')
    cursor = conn.cursor()
    query = """INSERT IGNORE INTO articles (source, author, title, description, url, urlToImage, publishedAt, content) 
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
    cursor.execute(query, tuple(data.values()))
    conn.commit()
    conn.close()

def find_author(soup):
    selectors = [
        {'type': 'meta', 'attr': {'name': 'author'}},
        {'type': 'span', 'attr': {'class': 'autor'}},
        {'type': 'div', 'attr': {'class': 'nume-autor'}},
        {'type': 'a', 'attr': {'class': 'author-name'}},
        {'type': 'p', 'attr': {'class': 'author'}}
    ]
    
    for s in selectors:
        if s['type'] == 'meta':
            res = soup.find('meta', s['attr'])
            if res and res.get('content'):
                return res.get('content').strip()
        else:
            res = soup.find(s['type'], s['attr'])
            if res and res.text.strip():
                return res.text.strip()
    return 'Anonim'

def scrape_article(url):
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')

    data = {
    'source': soup.find('meta', property='og:site_name')['content'] if soup.find('meta', property='og:site_name') else 'SursaNecunoscuta',
    
    'author': find_author(soup),
    
    'title': soup.find('h1').text.strip() if soup.find('h1') else 'Fără titlu',
    'description': '', 
    'url': url,
    'urlToImage': soup.find('meta', property='og:image')['content'] if soup.find('meta', property='og:image') else '',
    
    'publishedAt': (soup.find('meta', property='article:published_time')['content'][:19].replace('T', ' ') 
                    if soup.find('meta', property='article:published_time') 
                    else datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
    
    'content': ' '.join([p.text for p in soup.find_all('p')])[:1000]
}
    
    data['description'] = generate_summary(data['content'])

    print("---------------------------------------------------------------------------------------------------------------------------------------------")
    print(data)
    save_to_db(data)
    print(f"# Am procesat stirea cu urmatorul titlu: {data['title']} #")
    print("---------------------------------------------------------------------------------------------------------------------------------------------")
    print("\n")

# exemplu utilizare
scrape_article("https://www.mediafax.ro/politic/grindeanu-spune-ca-e-de-acord-cu-propunerile-facute-de-varujan-pambuccian-si-kelemen-hunor-privind-noul-guvern-23771576")
scrape_article("https://stirileprotv.ro/stiri/inspectorul-pro/polite-rca-false-pe-strazile-din-romania-brokerita-recunoaste-nu-ma-inteleg-pe-mine-cum-de-tot-fac-asta-asf-se-balbaie.html")