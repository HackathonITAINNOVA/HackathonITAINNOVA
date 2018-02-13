from bs4 import BeautifulSoup
import re
import requests

from . import config
import logging
logger = logging.getLogger(__name__)


ELEMENTS = ["li", "footer", "header", "nav", "aside", "figure", "blockquote", "img"]

WORDS = ["image", "img", "footer", "pie", "banner", "autoria",
         "cookie", "themes", "foto", "media", "encabezado", "registro",
         "entradilla", "telefono", "comment", "hidden", "dialog", "fail",
         "fecha", "tweet", "twitter", "comentario", "date"]

STYLES = ["text-align: center", "display: none"]


def delete_attrs(soup, words):
    for word in words:
        for t in soup.find_all(attrs=re.compile(word, re.IGNORECASE)):
            t.extract()
        for t in soup.find_all(attrs={'id': re.compile(word, re.IGNORECASE)}):
            t.extract()


def delete_elements(soup, elements):
    for element in elements:
        for t in soup.find_all(element):
            t.extract()


def delete_styles(soup, styles):
    for style in styles:
        style = style.replace(" ", "\s*")
        for t in soup.find_all(style=re.compile(style, re.IGNORECASE)):
            t.extract()


def fetch_url(url):
    text = None
    logger.debug("Requesting html from ulr " + url)
    try:
        response = requests.get(url, proxies=config.private.PROXY, verify=False)
        response.raise_for_status()
    except requests.HTTPError:
        logger.error("Clean html request failed with status code {}".format(response.status_code))
        logger.error("for url: " + url)
    except requests.RequestException:
        logger.exception("Clean html request failed")
    else:
        text = response.text

    return text or ""


def filter_html(html):
    text = ""

    soup = BeautifulSoup(html, "html.parser")

    delete_elements(soup, ELEMENTS)
    delete_attrs(soup, WORDS)
    delete_styles(soup, STYLES)
    paragraphs = soup.find_all('p')

    matches = []
    for p in paragraphs:
        if not any(p in m.descendants for m in paragraphs):
            matches.append(p)

    for m in matches:
        if len(m.text) > 100:
            text += m.text + " "

    return text


def remove_html_tags(html):
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', html)

    cleantext.replace("\n", " ")
    cleantext.replace("\t", " ")
    return re.sub(r'\s+', ' ', cleantext)


def remove_urls(text):
    PATTERN = r"http\S+"
    return re.sub(PATTERN, '', text)


def get_hashtags(text):
    PATTERN = r"#\S+"
    return re.findall(PATTERN, text)


def get_domain(url):
    PATTERN = r"^(?:https?:\/\/)?(?:[^@\/\n]+@)?(?:www\.)?([^:\/\n]+)"
    return re.match(PATTERN, url)[1]