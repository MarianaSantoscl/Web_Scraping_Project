import requests
from bs4 import BeautifulSoup
import pymysql.cursors
from datetime import datetime, timedelta
import re

# Função para conectar ao banco de dados MySQL
def connect_to_db():
    return pymysql.connect(
        host='localhost',
        user='username',
        password='your_password',
        database='web_scraping',
        cursorclass=pymysql.cursors.DictCursor  # Utilizando cursor do tipo dicionário para facilitar a manipulação dos resultados
    )

# Função para inserir dados no banco de dados
def insert_article(cursor, title, author, publication_date, content):
    cursor.execute(
        "INSERT INTO articles (title, author, publication_date, content) VALUES (%s, %s, %s, %s)",
        (title, author, publication_date, content)
    )

# Função para converter a data de publicação para o formato desejado
def parse_relative_date(date_str):
    now = datetime.now()
    match = re.match(r"(\d+)\s*(\w+)", date_str)
    if match:
        value, unit = int(match.group(1)), match.group(2)
        if 'min' in unit:
            return now - timedelta(minutes=value)
        elif 'hr' in unit or 'hour' in unit:
            return now - timedelta(hours=value)
        elif 'day' in unit:
            return now - timedelta(days=value)
    return now

# Função para buscar autor na página do artigo
def get_article_author(article_url):
    response = requests.get(article_url)
    article_soup = BeautifulSoup(response.content, 'html.parser')
    author_tag = article_soup.find('span', {'data-testid': 'byline-name'})
    if author_tag:
        return author_tag.text.strip()
    return "BBC News"

# Função para buscar data de publicação
def get_article_date(article_soup):
    date_tag = article_soup.find('span', {'data-testid': 'card-metadata-lastupdated'})
    if date_tag:
        return parse_relative_date(date_tag.text.strip())
    return datetime.now()

# Função principal de web scraping
def scrape_articles():
    connection = connect_to_db()
    cursor = connection.cursor()
    with cursor:
        url = 'https://www.bbc.com/news/world'
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Selecionar artigos da seção "World"
        articles = soup.find_all('div', attrs={'data-testid': 'edinburgh-card'})

        # Loop para extrair informações de cada artigo
        for article in articles:
            anchor = article.find('a', {'data-testid': 'internal-link', 'class': 'sc-2e6baa30-0 gILusN'})
            if anchor and 'href' in anchor.attrs:
                link = 'https://www.bbc.com' + anchor['href']
                print(link)
                title_tag = article.find('h2', {'data-testid': 'card-headline'})
                content_tag = article.find('p', attrs={'data-testid': 'card-description'})

                # Extraindo o título do artigo
                title = title_tag.get_text() if title_tag else 'No title'

                # Extraindo o conteúdo do artigo
                content = content_tag.get_text() if content_tag else 'No content'

                # Acessar página do artigo para obter o autor
                author = get_article_author(link)

                # Obter data de publicação relativa
                publication_date = get_article_date(article)

                # Logging para depuração
                print(f"Title: {title}")
                print(f"Author: {author}")
                print(f"Publication Date: {publication_date}")
                print(f"Content: {content}")
                print("-----------")

                insert_article(cursor, title, author, publication_date, content)

        connection.commit()
        cursor.close()
        connection.close()


if __name__ == '__main__':
    scrape_articles()
    print("Scraping completed and data stored in the database.")
