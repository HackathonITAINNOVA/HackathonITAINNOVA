from bs4 import BeautifulSoup
import re
import requests
import html

from . import config
import logging
logger = logging.getLogger(__name__)


ELEMENTS = ["li", "footer", "header", "nav", "aside", "figure", "blockquote", "img"]

WORDS = [re.compile(w, re.IGNORECASE)
         for w in ["image", "img", "footer", "pie", "banner", "autoria", "cookie", "themes", "foto",
                   "encabezado", "registro", "entradilla", "telefono", "comment", "hidden",
                   "dialog", "fail", "fecha", "tweet", "twitter", "comentario", "date", "ColumnaDerecha",
                   "uh-cont2"]]

STYLES = [re.compile(s.replace(" ", "\s*"), re.IGNORECASE)
          for s in ["text-align: center", "display: none"]]

URL_REGEX = re.compile(r'''
    (?P<full>
        (?P<protocol>https?:\/\/)
        (www.)?
        (?P<domain>[\w.-]+?
        (?P<tld>(\.[\w]{2,3})+))
        (?P<path>\/[\w.-\/]+)?
    )
    ''', re.X)

HASHTAG_REGEX = re.compile(r'''
    (?P<full>\#
        (?P<word>\S+)\b
    )
    ''', re.X)

TWITTER_USER_REGEX = re.compile(r'''
    (?P<full>@
        (?P<user>\S+)\b)
    ''', re.X)

HTML_TAGS_REGEX = re.compile(r'<.*?>')

HTML_SCRIPTS_REGEX = re.compile(r'<script.*?\/script>', re.IGNORECASE)

URL_STRING = '<a href="{}" target="_blank">{}</a>'


def delete_attrs(soup):
    for word in WORDS:
        for t in soup.find_all(attrs=word):
            t.extract()
        for t in soup.find_all(attrs={'id': word}):
            t.extract()


def delete_elements(soup):
    for element in ELEMENTS:
        for t in soup.find_all(element):
            t.extract()


def delete_styles(soup):
    for style in STYLES:
        for t in soup.find_all(style=style):
            t.extract()


def fetch_url(url):
    text = None
    logger.info("Requesting html from ulr " + url)
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

    delete_elements(soup)
    delete_attrs(soup)
    delete_styles(soup)
    paragraphs = soup.find_all('p')

    matches = []
    for p in paragraphs:
        if not any(p in m.descendants for m in paragraphs):
            matches.append(p)

    for m in matches:
        if len(m.text) > 100:
            text += str(m)

    return text


def remove_html_tags(text):
    text = re.sub(HTML_TAGS_REGEX, '', text)

    text.replace("\n", " ")
    text.replace("\t", " ")

    text = html.unescape(text)
    return re.sub(r'\s+', ' ', text)


def parse_link(url):
    """Gives the parsed content a quoted style."""
    text = filter_html(fetch_url(url))
    return '<div class="alert alert-info">{}</div>'.format(text) if text else ""


def get_urls(text):
    return [match['full'] for match in URL_REGEX.finditer(text)]


def remove_urls(text):
    return URL_REGEX.sub('', text)


def linkify_urls(text):
    return URL_REGEX.sub(URL_STRING.format('\g<full>', '\g<full>'), text)


def get_hashtags(text):
    return [match['full'] for match in HASHTAG_REGEX.finditer(text)]


def linkify_hashtags(text, source):
    if source == 'facebook':
        link = 'https://www.facebook.com/hashtag/'
    if source == 'twitter':
        link = 'https://twitter.com/hashtag/'
    return HASHTAG_REGEX.sub(URL_STRING.format(link + '\g<word>', '\g<full>'), text)


def linkify_twitter_users(text):
    return TWITTER_USER_REGEX.sub(URL_STRING.format('https://twitter.com/' + '\g<user>', '\g<full>'), text)


def get_domain(url):
    return URL_REGEX.match(url)['domain']


def remove_scripts(text):
    return HTML_SCRIPTS_REGEX.sub('', text)
