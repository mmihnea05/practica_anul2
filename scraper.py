from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
import mysql.connector
import ollama
from datetime import datetime
from dateutil import parser
import re

def generate_summary(text):
    try:
        response = ollama.chat(model='llama3.2', messages=[
            {'role': 'user', 'content': f'Genereaza o descriere scurta (max 200 caractere) pentru: {text[:1000]}'}
        ])
        return response['message']['content']
    except Exception:
        return text[:197] + "..."
    
def generate_category(url):
    prompt = (
        f"Intra pe urmatorul website: {url} si alege categoria acestei stiri dintre urmatoarele: "
        f"Sanatate, Politica, Economie, Finante, Actualitate, Sport, Meteo, Monden, Divertisment, "
        f"Tehnologie, Educatie, Auto. Foarte IMPORTANT, raspunde intr-un singur cuvant si alege "
        f"strict din categoriile precizate mai sus."
    )
    
    try:
        response = ollama.chat(model='llama3.2', messages=[{'role': 'user', 'content': prompt}])
        return response['message']['content'].strip().rstrip('.')
    except Exception:
        return "Actualitate"

def save_to_db(data):
    conn = mysql.connector.connect(host='localhost', user='admin', password='admin', database='news_db')
    cursor = conn.cursor()
    query = """INSERT IGNORE INTO articles (source, author, title, category, description, url, urlToImage, publishedAt, content) 
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"""
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

        # Agerpres
        if '  ' in date_str:
            parts = date_str.split('  ')
            if len(parts) >= 2:
                data, ora = parts[0].strip(), parts[1].strip()
                zi, luna, an = data.split('-')
                return f"{an}-{luna.zfill(2)}-{zi.zfill(2)} {ora}:00"

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
    # agerpres
    paragraphs = soup.find_all('p')
    for p in paragraphs:
        text = p.get_text()
        match = re.search(r'editor(?![\s-]online):\s*([^,)]+)', text, re.IGNORECASE)
        if match:
            return match.group(1).strip()

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

def find_title(soup):
    og_title = soup.find('meta', property='og:title')
    if og_title and og_title.get('content'):
        return og_title['content'].strip()

    h1_element = soup.find('h1')
    if h1_element:
        return h1_element.get_text(strip=True)

    if soup.title and soup.title.string:
        return soup.title.string.strip()

    return 'Fără titlu'

def find_source(soup, url):
    if 'stirileprotv.ro' in url:
        return "StirilePROTV"
    if 'digi24.ro' in url:
        return "Digi24"
    if 'antena3.ro' in url:
        return "Antena3 CNN"
    if 'libertatea.ro' in url:
        return "Libertatea"
    if 'hotnews.ro' in url:
        return "HotNews"
    if 'economedia.ro' in url:
        return "Economedia"
    if 'profit.ro' in url:
        return "Profit"
    if 'zf.ro' in url:
        return "Ziarul Financiar"
    if 'mediafax.ro' in url:
        return "Mediafax"
    if 'agerpres.ro' in url:
        return "Agerpres"

    og_site = soup.find('meta', property='og:site_name')
    if og_site and og_site.get('content'):
        return og_site.get('content').strip()
    
    return 'SursaNecunoscuta'

def find_category(soup, url):
    # pro tv
    if 'stirileprotv.ro' in url:
        category_div = soup.find('div', class_='article--section-information')
        if category_div:
            link = category_div.find('a')
            if link:
                return link.get_text(strip=True)
        
    # digi24
    if 'digi24.ro' in url:
        parsed_url = urlparse(url)
        path_parts = parsed_url.path.strip('/').split('/')
        if len(path_parts) >= 2 and path_parts[0] == 'stiri':
            return path_parts[1].replace('-', ' ').capitalize()
        
    # antena3cnn + mediafax
    if 'antena3.ro' in url or 'mediafax.ro' in url:
        parsed_url = urlparse(url)
        path_parts = parsed_url.path.strip('/').split('/')
        return path_parts[0].replace('-', ' ').capitalize()
    
    # libertatea
    if 'libertatea.ro' in url:
        breadcrumbs = soup.find('span', class_='breadcrumbs')
        if breadcrumbs:
            links = breadcrumbs.find_all('a')
            if len(links) >= 3:
                # home | stiri | categorie
                # links[-1] extrage ultimul element care este categoria
                return links[-1].get_text(strip=True)
            elif len(links) >= 2:
                return links[-1].get_text(strip=True)
            
    # hotnews
    if 'hotnews.ro' in url:
        section_meta = soup.find('meta', property='article:section')
        if section_meta and section_meta.get('content'):
            return section_meta['content'].strip()
    
    # economedia
    if 'economedia.ro' in url:
        breadcrumbs = soup.find('div', class_='single__breadcrumbs')
        if breadcrumbs:
            links = breadcrumbs.find_all('a')
            if links:
                return links[-1].get_text(strip=True)
            
    # profit
    if 'profit.ro' in url:
        category_link = soup.find('a', class_='art-categ')
        if category_link:
            return category_link.get_text(strip=True)
        
    # zf
    if 'zf.ro' in url:
        return generate_category(url) # folosim llama3.2 pentru a determina categoria pe baza URL-ului
    
    # Agerpres
    if 'agerpres.ro' in url:
        flux_label = soup.find(string=lambda text: text and 'Flux:' in text)
        if flux_label:
            parent = flux_label.parent
            category_link = parent.find_next('a')
            if category_link:
                return category_link.get_text(strip=True)

    return 'General'

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
        
    # Agerpres
    agerpres_date = soup.find('li', class_='article-date')
    if agerpres_date:
        raw_text = agerpres_date.get_text(strip=True).replace('Data:', '').strip()
        return parse_to_datetime(raw_text)
    
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def scrape_article(url):
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')

    data = {
    'source': find_source(soup, url),
    'author': find_author(soup),
    'title': find_title(soup),
    'category': find_category(soup, url),
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

def get_links_from_file(file_path):
    links_list = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            links_list = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"Eroare: Fișierul '{file_path}' nu a fost găsit.")
    
    return links_list


# exemplu utilizare
#links= get_links_from_file('links.txt')
#for url in links:
 #   try:
  #      scrape_article(url) 
   # except Exception as e:
    #    print(f"Eroare la procesarea {url}: {e}")

















# exemplu utilizare
scrape_article("https://stirileprotv.ro/stiri/international/politico-o-ancheta-de-corup-ie-a-declansat-remanierea-surprinzatoare-a-cabinetului-ucrainean-decisa-de-zelenski.html")
scrape_article("https://www.digi24.ro/stiri/externe/mapamond/donald-trump-sustine-ca-sua-ar-trebui-sa-controleze-stramtoarea-ormuz-si-ameninta-iranul-o-sa-i-lovim-foarte-tare-3860305")
scrape_article("https://www.antena3.ro/sport/noua-tari-din-ue-inclusiv-romania-solicita-reducerea-finantarii-comitetului-olimpic-international-din-cauza-reprimirii-rusilor-795622.html")
scrape_article("https://www.libertatea.ro/stiri/stiri-brasov-fabrica-purolite-brasov-investeste-560000-euro-sistem-tratare-apa-5814473")
scrape_article("https://hotnews.ro/sorin-grindeanu-virulent-la-adresa-pnl-usr-ne-vom-bate-cu-aceasta-pesta-a-hastagilor-pe-tot-terenul-2299618")
scrape_article("https://economedia.ro/mercedes-benz-anunta-ca-a-investit-un-miliard-de-euro-pentru-a-dubla-capacitatea-fabricii-din-kecskemet.html")
scrape_article("https://profit.ro/povesti-cu-profit/energie/pas-inainte-dupa-esec-complexul-energetic-oltenia-si-alro-slatina-pas-inainte-pentru-baterii-de-950-mw-langa-fotovoltaicele-ceo-omv-petrom-tinmar-dupa-esecul-centralei-pe-gaze-naturale-22515087")
scrape_article("https://www.zf.ro/carturesti-se-extinde-in-audio/mihaela-pana-post-merger-integration-manager-audiotribe-roman-marile-23190496")
scrape_article("https://www.mediafax.ro/politic/grindeanu-spune-ca-e-de-acord-cu-propunerile-facute-de-varujan-pambuccian-si-kelemen-hunor-privind-noul-guvern-23771576")
scrape_article("https://agerpres.ro/2026/07/09/reportaj-covasna-drumul-matasii-nilul-si-mostenirea-unui-calator---karda-zoltan--1574639")
scrape_article("https://agerpres.ro/social/2026/07/13/buzau-31-de-proiectile-de-artilerie-descoperite-pe-un-santier--1575719")