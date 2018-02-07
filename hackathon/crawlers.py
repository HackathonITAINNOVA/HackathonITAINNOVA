import facebook
from urllib.parse import parse_qs, urlparse
from urllib.request import ProxyHandler
import tweepy
from datetime import datetime
import feedparser

from .clean_html import remove_urls, get_hashtags, clean_url, remove_html_tags, get_domain
from . import config
import logging
logger = logging.getLogger(__name__)


class Facebook(object):
    APP_ID = config.private.FB_APP_ID
    APP_SECRET = config.private.FB_APP_SECRET
    ACCESS_TOKEN = config.private.FB_ACCESS_TOKEN
    DEFAULT_FIELDS = 'link,description,message,permalink_url,created_time,reactions,shares,from,parent_id'

    def __init__(self):
        self.api = facebook.GraphAPI(self.ACCESS_TOKEN, version='2.7')

    def _get_all_connections(self, id, connection_name, limit=10, **kwargs):
        """Get all pages from a get_connections call
        This will iterate over all pages returned by a get_connections call
        and yield the individual items.
        """
        count = 0
        while True:
            page = self.api.get_connections(id, connection_name, **kwargs)
            for post in page['data']:
                yield post
                count += 1
                if count == limit:
                    return
            next = page.get('paging', {}).get('next')
            if not next:
                return
            args = parse_qs(urlparse(next).query)
            del args['access_token']

    def get_interests(self):
        likes = self._get_all_connections('me', 'likes')
        return likes

    def get_feed(self, id, **kwargs):
        feed = self._get_all_connections(id, 'feed', fields=self.DEFAULT_FIELDS, **kwargs)
        return feed

    def get_docs_from_interests(self, **kwargs):
        for page in self.get_interests():
            for post in self.get_feed(page['id'], **kwargs):
                document = self.build_document(page, post, type='interest')
                # Only return document if text is not empty
                if document['text']:
                    yield document
                else:
                    logger.info("Post without text discarded")

    def get_docs_from_home_feed(self, **kwargs):
        me = self.api.get_object('me')
        for post in self.get_feed('me', **kwargs):
            document = self.build_document(me, post, type='profile')
            # Only return document if text is not empty
            if document['text']:
                yield document
            else:
                logger.info("Post without text discarded")

    def get_all_docs(self, **kwargs):
        yield from self.get_docs_from_interests(**kwargs)
        yield from self.get_docs_from_home_feed(**kwargs)

    @classmethod
    def build_document(cls, page, post, **kwargs):
        logger.info("Processing fb post " + post['id'])
        logger.debug(post)
        doc = {
            'documentID': 'FB_' + post['id'],
            'collectorID': 'facebook',

            'sourceId': page['id'],
            'sourceName': page['name'],

            'text': remove_urls((post.get('message', '') + post.get('description', '')).replace("\n", " ")),

            'createdAt': cls.format_date(post['created_time']),
            'url': post['permalink_url'],
            'postID': post['id'],
            'postUserId': post['from']['id'] if 'from' in post else '',
            'postUserName': post['from']['name'] if 'from' in post else '',

            'links': post.get('link'),
            'shares': post['shares']['count'] if 'shares' in post else 0,
            'isShared': bool(post.get('parent_id'))
        }
        doc['hashtagEntities'] = get_hashtags(doc['text'])
        doc.update(cls.count_reactions(post))
        doc.update(kwargs)

        logger.debug("Finished building document " + doc['documentID'])
        logger.debug(doc)
        return doc

    @staticmethod
    def count_reactions(post):
        counter = {
            "LOVE": 0,
            "HAHA": 0,
            "LIKE": 0,
            "SAD": 0,
            "ANGRY": 0,
            "WOW": 0
        }
        if 'reactions' in post:
            for reaction in post["reactions"]["data"]:
                counter[reaction["type"]] += 1
        counter['popularity'] = sum(counter.values())
        return counter

    @staticmethod
    def format_date(date):
        return datetime.strptime(date, '%Y-%m-%dT%H:%M:%S%z')


class Twitter(object):
    CONSUMER_KEY = config.private.TW_CONSUMER_KEY
    CONSUMER_SECRET = config.private.TW_CONSUMER_SECRET
    ACCESS_TOKEN = config.private.TW_ACCESS_TOKEN
    ACCESS_SECRET = config.private.TW_ACCESS_SECRET

    def __init__(self):
        auth = tweepy.OAuthHandler(self.CONSUMER_KEY, self.CONSUMER_SECRET)
        auth.set_access_token(self.ACCESS_TOKEN, self.ACCESS_SECRET)
        self.api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)
        self.username = self.api.auth.get_username()

    def get_home(self, limit=100, since_id=None):
        return (status._json for status in tweepy.Cursor(self.api.home_timeline, since_id).items(limit))

    def get_all_docs(self, **kwargs):
        return (self.build_document(self.username, tweet) for tweet in self.get_home(**kwargs))

    @classmethod
    def build_document(cls, username, tweet):
        logger.info("Processing tweet " + tweet['id_str'])
        logger.debug(tweet)
        links = [url['expanded_url'] for url in tweet['entities']['urls']]
        texts = [tweet['text']] + [clean_url(link) for link in links]
        doc = {
            'documentID': 'TW_' + tweet['id_str'],
            'collectorID': 'twitter',

            'sourceId': tweet['retweeted_status']['user']['screen_name'] if tweet['retweeted'] else '',
            'sourceName': tweet['retweeted_status']['user']['name'] if tweet['retweeted'] else '',

            'text': ". ".join(remove_urls(text) for text in texts),

            'createdAt': cls.format_date(tweet['created_at']),
            'url': 'https://twitter.com/' + tweet["user"]["screen_name"] + '/status/' + tweet['id_str'],
            'postID': tweet['id'],
            'postUserId': tweet['user']['screen_name'],
            'postUserName': tweet['user']['name'],

            'links': links,
            'hashtagEntities': [hashtag['text'] for hashtag in tweet['entities']['hashtags']],
            'isShared': tweet['retweeted']
        }

        doc['type'] = 'profile' if doc['postUserId'] == username else 'interest'

        logger.debug("Finished building document " + doc['documentID'])
        logger.debug(doc)
        return doc

    @staticmethod
    def format_date(date):
        return datetime.strptime(date, "%a %b %d %H:%M:%S %z %Y")


class RSS(object):
    PROXY = config.settings.PROXY
    FEEDS_URL = config.settings.FEEDS_URL

    def __init__(self):
        self.proxy = ProxyHandler(self.PROXY)

    def get_sources(self):
        return (feedparser.parse(url, handlers=[self.proxy]) for url in self.FEEDS_URL)

    def get_all_docs(self, limit, since):
        for source in self.get_sources():
            logger.info("Source: {}".format(source.href))
            for count, entry in enumerate(source.entries):
                logger.info("Entry: {}".format(entry.link))

                if limit and count == limit:
                    logger.info("Entry discarded by limit")
                    break

                document = self.build_document(source.feed, entry)

                if since and document['createdAt'].isoformat() < since:
                    logger.info("Entry discarded by date")
                    break

                yield document

    @classmethod
    def build_document(cls, feed, entry):
        logger.info("Processing feed {}: {}".format(feed.title, entry.title))
        logger.debug(entry.summary)
        doc = {
            'documentID': 'RSS_' + entry.get('id', entry.link),
            'collectorID': 'rss',

            'sourceId': get_domain(feed.link),
            'sourceName': feed.title,

            'text': remove_html_tags(entry.content[0].value if 'content' in entry else entry.summary),

            'url': entry.link,
            'postID': entry.get('id', entry.link),
            'postUserId': entry.get('author', ''),
            'postUserName': entry.get('author', ''),

            'hashtagEntities': [tag['term'] for tag in entry.get('tags', [])],
            'links': [link['href'] for link in entry.links if link['type'] == 'text/html']
            # 'links': [link['href'] for link in entry.links[1:] if link['type'] == 'text/html']
        }

        date = None
        if 'published_parsed' in entry:
            date = entry.published_parsed
        elif 'updated_parsed' in entry:
            date = entry.updated_parsed

        doc['createdAt'] = datetime(*date[:6]) if date else "NOW"

        logger.debug("Finished building document " + doc['documentID'])
        logger.debug(doc)
        return doc

    # def parse_date(date):
    #     try:
    #         obj = datetime.strptime(date, "%a, %d %b %Y %H:%M:%S %z")
    #         return obj.strftime("%Y-%m-%dT%H:%M:%SZ")
    #     except ValueError:
    #         obj = datetime.strptime(date, "%a, %d %b %Y %H:%M:%S %Z")
    #         return obj.strftime("%Y-%m-%dT%H:%M:%SZ")

    # def parse_one_xml(url):
    #     ret = []
    #     xml = requests.get(url, proxies=config.settings.PROXY).text
    #     soup = BeautifulSoup(xml, "xml")
    #     for i in soup.find_all("item"):
    #         # try:
    #         text = i.find("content:encoded").text
    #         #text = html2text(text)
    #         text = clean_html_text(text)
    #         retWF = call_WF2(text)
    #         if retWF:
    #             date = RSS.parse_date(i.find("pubDate").text)
    #             doc = {
    #                 "createdAt": date,
    #                 "collectorID": "rss",
    #                 "url": i.find("link").text,
    #                 "text": text
    #             }
    #             doc.update(retWF)
    #             ret.append(doc)
    #             print(doc)
    #             s = Solr()
    #             # s.insert(doc)
    #         # except:
    #         #     print("Error parsing, skipping to the next")
    #         #     print(i, sys.exc_info()[0])
    #         #     print("---------------")
    #     return ret

    # def parse_xml(self, urls):
    #     ret = []
    #     for url in urls:
    #         ret.append(RSS.parse_one_xml(url))
    #     return ret


if __name__ == '__main__':
    tw = Twitter()
    fb = Facebook()
    rss = RSS()
