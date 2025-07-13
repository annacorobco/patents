import os
import re
import time
import html
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from elasticsearch_dsl.connections import connections
from elasticsearch.helpers import bulk

from documents import JustiaPatents

ES_HOST = os.getenv("ES_HOST")
ES_PORT = os.getenv("ES_PORT")
BASE_URL = "https://patents.justia.com"
SESSION = requests.Session()

DATA = []
BATCH_SIZE = 100
ES_CONNECTED = False
TOTAL_INSERTED = 0


def log(msg):
    print(f"[LOG] {msg}")


def clean_html_fragments(fragments):
    return html.unescape(
        re.sub(r"\s+", " ", " ".join(fragments)).encode("ascii", "ignore").decode()
    ).strip()


def clean_text(text):
    if not text:
        return None
    return re.sub(r"\s+", " ", text.replace(":", "")).encode("ascii", "ignore").decode().strip()


def connect_to_es():
    global ES_CONNECTED
    if not ES_CONNECTED:
        connections.create_connection(hosts=f"{ES_HOST}:{ES_PORT}", verify_certs=False)
        log("Connected to Elasticsearch")
        ES_CONNECTED = True


def fetch_html(url):
    response = SESSION.get(url)
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")


def bulk_insert(docs):
    try:
        bulk(connections.get_connection(), docs, index=JustiaPatents.Index.name, doc_type='_doc')
        log(f"Inserted {len(docs)} documents")
    except Exception as ex:
        log(f"Bulk insert failed: {ex}")
        time.sleep(300)


def process_patent_page(url):
    global DATA, TOTAL_INSERTED

    soup = fetch_html(url)
    connect_to_es()

    def extract_text(selector):
        el = soup.select_one(selector)
        return clean_text(el.get_text(strip=True)) if el else None

    def extract_html(selector):
        elements = soup.select(selector)
        return clean_html_fragments([el.decode() for el in elements])

    title = extract_text("h1.heading-1")
    filed_raw = soup.select_one("#byline time")
    filed = datetime.strptime(filed_raw.get_text(strip=True), "%b %d, %Y").strftime("%Y-%m-%d") if filed_raw else None
    company = soup.select_one("#byline time + a")
    company_text = company.get_text(strip=True) if company else None

    doc = {
        '_op_type': 'update',
        '_index': JustiaPatents.Index.name,
        '_type': '_doc',
        '_id': extract_text("strong:contains('Patent number') ~ *") or extract_text("strong:contains('Publication number') ~ *"),
        'doc_as_upsert': True,
        'doc': {
            'url': url,
            'title': title,
            'filed': filed,
            'company': company_text,
            'company_latest_patents': extract_html("#company-latest .wrap:not(.title-wrapper)"),
            'abstract': extract_text("#abstract p"),
            'description': extract_html("#description"),
            'claims': extract_html("#claims .wrap"),
            'citations': extract_html("#citations .wrap"),
            'patent_number': extract_text("strong:contains('Patent number') ~ *"),
            'type': extract_text("strong:contains('Type') ~ *"),
            'publication_number': extract_text("strong:contains('Publication number') ~ *"),
            'date_of_patent': None,
            'assignee': clean_text(" ".join([el.get_text(strip=True) for el in soup.select("strong:contains('Assignee') ~ a, strong:contains('Assignee') ~ text")])),
            'inventor': clean_text(" ".join([el.get_text(strip=True) for el in soup.select("strong:contains('Inventor') ~ a, strong:contains('Inventor') ~ text")])),
            'primary_examiner': extract_text("strong:contains('Primary Examiner') ~ a"),
            'assistant_examiner': extract_text("strong:contains('Assistant Examiner') ~ a"),
            'application_number': extract_text("strong:contains('Application Number') ~ *"),
            'classifications': extract_html("#classifications .wrap"),
        }
    }

    date_of_patent = extract_text("strong:contains('Date of Patent') ~ *")
    if date_of_patent:
        try:
            doc['doc']['date_of_patent'] = datetime.strptime(date_of_patent, "%b %d, %Y").strftime("%Y-%m-%d")
        except:
            pass

    DATA.append(doc)

    if len(DATA) >= BATCH_SIZE:
        bulk_insert(DATA)
        TOTAL_INSERTED += len(DATA)
        DATA = []


def crawl_patent_links(issue_url):
    soup = fetch_html(issue_url)
    links = [a['href'] for a in soup.select("#search-results a") if a.get("href")]
    for path in links:
        process_patent_page(BASE_URL + path)

    next_page = soup.select_one(".pagination a:contains('next')")
    if next_page and next_page.get("href"):
        crawl_patent_links(BASE_URL + next_page["href"])


def crawl_date_pages(year_url):
    soup = fetch_html(year_url)
    links = [a['href'] for a in soup.select("ul.list-columns-three a") if a.get("href")]
    for path in links:
        crawl_patent_links(BASE_URL + path)


def crawl_years():
    soup = fetch_html(BASE_URL + "/patents-by-issue-date")
    links = [a['href'] for a in soup.select("ul.list-columns-three a") if a.get("href")]
    for path in links:
        crawl_date_pages(BASE_URL + path)

    if DATA:
        bulk_insert(DATA)
        log(f"Final flush: {len(DATA)} documents")
        DATA.clear()


if __name__ == "__main__":
    crawl_years()
    log(f"Finished. Total documents inserted: {TOTAL_INSERTED}")
