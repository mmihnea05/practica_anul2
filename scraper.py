import requests
from bs4 import BeautifulSoup
import mysql.connector
import ollama
from datetime import datetime
from dateutil import parser

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

def parse_to_datetime(date_str):
    # Dictionar pentru luni
    luni = {'ian.': '01', 'feb.': '02', 'mar.': '03', 'apr.': '04', 'mai': '05', 'iun.': '06', 
            'iul.': '07', 'aug.': '08', 'sep.': '09', 'oct.': '10', 'noi.': '11', 'dec.': '12'}
    
    try:
        if 'T' in date_str:
            # parser.parse descompune automat formatul ISO: 2026-07-13T21:30:00+03:00
            return parser.parse(date_str).strftime('%Y-%m-%d %H:%M:%S')

        # ProTV
        if ':' in date_str and '-' in date_str:
            return date_str
            
        # 2. Ziarul Financiar
        if ',' in date_str:
            clean_str = date_str.replace(',', '').strip()
            parts = clean_str.split(' ')
            if len(parts) >= 2:
                data_part = parts[0] # "08.07.2026"
                ora_part = parts[1]  # "00:06"
                zi, luna, an = data_part.split('.')
                return f"{an}-{luna.zfill(2)}-{zi.zfill(2)} {ora_part}:00"
        
        # Mediafax
        parts = date_str.replace(',', '').split()
        if len(parts) >= 4:
            zi, luna_txt, an, ora = parts[0], parts[1], parts[2], parts[3]
            luna = luni.get(luna_txt.lower(), '01')
            return f"{an}-{luna}-{zi.zfill(2)} {ora}:00"
            
    except Exception:
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def find_author(soup):
    profit_author = soup.find('strong', class_='art-author')
    if profit_author:
        autor_link = profit_author.find('a')
        if autor_link:
            return autor_link.get_text(strip=True)

    # hotnews
    for author_meta_name in ['parsely-author', 'author']:
        meta_author = soup.find('meta', attrs={'name': author_meta_name})
        if meta_author and meta_author.get('content'):
            return meta_author.get('content').strip()

    libertatea_element = soup.find('div', class_='box-authors')
    if libertatea_element:
        author_name_span = libertatea_element.find('span', class_='author-name')
        if author_name_span:
            return author_name_span.get_text(strip=True)

    # + antena3cnn
    mediafax_element = soup.find('span', class_='single__authors')
    if mediafax_element:
        autor_link = mediafax_element.find('a')
        if autor_link:
            return autor_link.text.strip()
        return mediafax_element.text.strip()

    protv_element = soup.find('div', class_='author--name')
    if protv_element:
        autor_link = protv_element.find('a')
        if autor_link:
            return autor_link.text.strip()
        return protv_element.text.strip()

    digi24_element = soup.find('a', href=lambda href: href and "/autor/" in href)
    if digi24_element:
        return digi24_element.get_text(strip=True)
        
    meta_author = soup.find('meta', {'name': 'author'})
    if meta_author and meta_author.get('content'):
        return meta_author.get('content').strip()

    return 'Anonim'

def find_source(soup, url):
    if 'stirileprotv.ro' in url:
        return "StirilePROTV"
    if 'digi24.ro' in url:
        return "Digi24"
    if 'antena3.ro' in url:
        return "Antena3 CNN"
    if 'mediafax.ro' in url:
        return "Mediafax"
    if 'libertatea.ro' in url:
        return "Libertatea"

    og_site = soup.find('meta', property='og:site_name')
    if og_site and og_site.get('content'):
        return og_site.get('content').strip()
    
    return 'SursaNecunoscuta'

def find_published_date(soup):
    og_pub = soup.find('meta', property='article:published_time')
    if og_pub and og_pub.get('content'):
        return parse_to_datetime(og_pub['content'])

    # ProTV + antena3cnn
    protv_date = soup.find('span', attrs={'data-utc-date': True})
    if protv_date:
        return parse_to_datetime(protv_date['data-utc-date'])

    # Mediafax
    mediafax_container = soup.find('div', class_='display-flex gap-5')
    if mediafax_container:
        raw_text = mediafax_container.get_text(separator='|', strip=True).split('|')[0].rstrip(',')
        return parse_to_datetime(raw_text)
    
    # Digi24
    digi_meta = soup.find('meta', attrs={'name': 'publish-date'})
    if digi_meta and digi_meta.get('content'):
        return parse_to_datetime(digi_meta['content'])
    
    # Ziarul Financiar
    zf_meta = soup.find('div', class_='rb-new-meta')
    if zf_meta:
        date_span = zf_meta.find('span')
        if date_span:
            raw_text = date_span.get_text(strip=True)
            return parse_to_datetime(raw_text)
    
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def scrape_article(url):
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')

    data = {
    'source': find_source(soup, url),
    
    'author': find_author(soup),
    
    'title': soup.find('h1').text.strip() if soup.find('h1') else 'Fără titlu',
    'description': '', 
    'url': url,
    'urlToImage': soup.find('meta', property='og:image')['content'] if soup.find('meta', property='og:image') else '',
    
    'publishedAt': find_published_date(soup),
    
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
scrape_article("https://www.digi24.ro/stiri/externe/mapamond/donald-trump-sustine-ca-sua-ar-trebui-sa-controleze-stramtoarea-ormuz-si-ameninta-iranul-o-sa-i-lovim-foarte-tare-3860305")
scrape_article("https://www.antena3.ro/life/travel/insula-din-grecia-unde-apa-marii-este-calda-aproape-tot-timpul-anului-iar-vantul-nu-bate-niciodata-795045.html")
scrape_article("https://www.libertatea.ro/stiri/stiri-brasov-fabrica-purolite-brasov-investeste-560000-euro-sistem-tratare-apa-5814473")
scrape_article("https://hotnews.ro/sorin-grindeanu-virulent-la-adresa-pnl-usr-ne-vom-bate-cu-aceasta-pesta-a-hastagilor-pe-tot-terenul-2299618")
scrape_article("https://economedia.ro/info-sud-est-cum-a-ratat-delta-dunarii-proiecte-pnrr-in-valoare-de-50-de-milioane-de-euro.html")
scrape_article("https://profit.ro/povesti-cu-profit/energie/pas-inainte-dupa-esec-complexul-energetic-oltenia-si-alro-slatina-pas-inainte-pentru-baterii-de-950-mw-langa-fotovoltaicele-ceo-omv-petrom-tinmar-dupa-esecul-centralei-pe-gaze-naturale-22515087")
scrape_article("https://www.zf.ro/carturesti-se-extinde-in-audio/mihaela-pana-post-merger-integration-manager-audiotribe-roman-marile-23190496")