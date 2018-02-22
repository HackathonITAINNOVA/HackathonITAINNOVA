import facebook
from urllib.parse import parse_qs, urlparse
from urllib.request import ProxyHandler
import tweepy
from datetime import datetime
import feedparser

from .clean_html import *
from . import config
import logging
logger = logging.getLogger(__name__)


class Facebook(object):
    APP_ID = config.private.FB_APP_ID
    APP_SECRET = config.private.FB_APP_SECRET
    ACCESS_TOKEN = config.private.FB_ACCESS_TOKEN
    DEFAULT_FIELDS = 'link,description,message,permalink_url,created_time,reactions.summary(1),shares,from,parent_id'
    REACTIONS_TYPE = ('LOVE', 'HAHA', 'LIKE', 'SAD', 'ANGRY', 'WOW')

    def __init__(self):
        self.api = facebook.GraphAPI(self.ACCESS_TOKEN, version='2.7')
        self.me = self.api.get_object('me', fields='name,link')

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
        likes = self._get_all_connections('me', 'likes', limit=0, fields='name,link')
        return likes

    def get_feed(self, id, **kwargs):
        feed = self._get_all_connections(id, 'posts', fields=self.DEFAULT_FIELDS, **kwargs)
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
        for post in self.get_feed('me', **kwargs):
            document = self.build_document(self.me, post, type='profile')
            # Only return document if text is not empty
            if document['text']:
                yield document
            else:
                logger.info("Post without text discarded")

    def get_all_docs(self, **kwargs):
        yield from self.get_docs_from_interests(**kwargs)
        yield from self.get_docs_from_home_feed(**kwargs)

    def build_document(self, page, post, **kwargs):
        logger.info("Processing fb post " + post['id'])
        logger.debug(post)

        textPost = post.get('message', "") or post.get('description', "")
        texts = [self.linkify(textPost)]
        link = post.get('link')
        if link:
            texts.append(parse_link(link))

        textRaw = "<br>".join(texts)
        text = remove_urls(remove_html_tags(textRaw))
        textSentiment = remove_urls(remove_html_tags(textPost))

        doc = {
            'documentID': 'FB_' + post['id'],
            'collectorID': 'facebook',

            'sourceId': page['id'],
            'sourceName': page['name'],
            'sourceUrl': page['link'],

            'textRaw': textRaw,
            'text': text,
            'textSentiment': textSentiment,

            'createdAt': self.format_date(post['created_time']),
            'url': post['permalink_url'],
            'postID': post['id'],
            'postUserId': post['from']['id'] if 'from' in post else '',
            'postUserName': post['from']['name'] if 'from' in post else '',

            'links': link,
            'shares': post['shares']['count'] if 'shares' in post else 0,
            'isShared': bool(post.get('parent_id')),
            'hashtagEntities': get_hashtags(text),
            'popularity': post['reactions']['summary']['total_count'],
        }

        doc.update(self.count_all_reactions(post['id']))
        # Sets type field
        doc.update(kwargs)

        logger.debug("Finished building document " + doc['documentID'])
        logger.debug(doc)
        return doc

    def count_all_reactions(self, post_id):
        logger.info("Counting reactions")
        # Fetch all reactions in a single request using Field Expansion and Field Aliases
        fields = ','.join(['reactions.type({}).summary(1).as({})'.format(reaction)
                           for reaction in self.REACTIONS_TYPE])

        response = self.api.get_object(post_id, fields=fields)

        reactions = {key: response[key]['summary']['total_count']
                     for key in self.REACTIONS_TYPE}

        logger.debug(reactions)
        return reactions

    @staticmethod
    def format_date(date):
        return datetime.strptime(date, '%Y-%m-%dT%H:%M:%S%z')

    @staticmethod
    def linkify(text):
        text = linkify_urls(text)
        text = linkify_hashtags(text, 'facebook')
        logger.debug("Linkified text: " + text)
        return text


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
        textTweet = tweet['text']
        texts = [cls.linkify(textTweet)] + [parse_link(link) for link in links]
        textRaw = " <br>".join(texts)
        text = remove_urls(remove_html_tags(textRaw))
        textSentiment = remove_urls(remove_html_tags(textTweet))

        isShared = 'retweeted_status' in tweet

        sourceId = tweet['user']['screen_name']
        sourceName = tweet['user']['name']

        doc = {
            'documentID': 'TW_' + tweet['id_str'],
            'collectorID': 'twitter',

            'sourceId': sourceId,
            'sourceName': sourceName,
            'sourceUrl': 'https://twitter.com/' + sourceId,

            'postUserId': tweet['retweeted_status']['user']['screen_name'] if isShared else sourceId,
            'postUserName': tweet['retweeted_status']['user']['name'] if isShared else sourceName,

            'textRaw': textRaw,
            'text': text,
            'textSentiment': textSentiment,

            'createdAt': cls.format_date(tweet['created_at']),
            'url': 'https://twitter.com/' + tweet["user"]["screen_name"] + '/status/' + tweet['id_str'],
            'postID': tweet['id'],
            'postUserId': tweet['user']['screen_name'],
            'postUserName': tweet['user']['name'],

            'links': links,
            'popularity': tweet.get('favorite_count', 0),
            'shares': tweet.get('retweet_count', 0),

            'hashtagEntities': ["#" + hashtag['text'] for hashtag in tweet['entities']['hashtags']],
            'isShared': isShared,
            'type': 'profile' if sourceId == username else 'interest',
        }

        logger.debug("Finished building document " + doc['documentID'])
        logger.debug(doc)
        return doc

    @staticmethod
    def format_date(date):
        return datetime.strptime(date, "%a %b %d %H:%M:%S %z %Y")

    @staticmethod
    def linkify(text):
        text = linkify_urls(text)
        text = linkify_hashtags(text, 'twitter')
        text = linkify_twitter_users(text)
        logger.debug("Linkified text: " + text)
        return text


class RSS(object):
    PROXY = config.private.PROXY
    FEEDS_URL = config.settings.FEEDS_URL

    def __init__(self):
        self.proxy = ProxyHandler(self.PROXY)

    def get_sources(self):
        return (feedparser.parse(url, handlers=[self.proxy]) for url in self.FEEDS_URL)

    def get_all_docs(self, limit, since):
        for source in self.get_sources():
            logger.info("Source: {}".format(source.get('href', '')))
            for count, entry in enumerate(source.get('entries', [])):
                logger.info("Entry: {}".format(entry.get('link', '')))

                if limit and count == limit:
                    logger.info("Entry discarded by limit")
                    break

                document = self.build_document(source.feed, entry)

                if since and document['createdAt'].isoformat() < since:
                    logger.info("Entry discarded by date")
                    break

                if document['text']:
                    yield document

    @classmethod
    def build_document(cls, feed, entry):
        logger.info("Processing feed {}: {}".format(feed.get('title'), entry.get('title')))
        logger.debug(entry)

        date = None
        if 'published_parsed' in entry:
            date = entry.published_parsed
        elif 'updated_parsed' in entry:
            date = entry.updated_parsed
        createdAt = datetime(*date[:6]) if date else datetime.now()

        textRaw = entry.content[0].value if 'content' in entry else entry.summary
        text = remove_urls(remove_html_tags(textRaw))

        domain = get_domain(feed.get('link', ''))

        doc = {
            'documentID': 'RSS_' + entry.get('id', entry.link),
            'collectorID': 'rss',

            'sourceId': domain,
            'sourceName': domain,
            'sourceUrl': feed.get('link', ''),

            'textRaw': textRaw,
            'text': text,
            'textSentiment': text,

            'createdAt': createdAt,
            'url': entry.get('link', ''),
            'postID': entry.get('id', entry.link),
            'postUserId': entry.get('author', ''),
            'postUserName': entry.get('author', ''),

            # 'hashtagEntities': [tag['term'] for tag in entry.get('tags', [])],
            'links': [link['href'] for link in entry.get('links', []) if link['type'] == 'text/html']
            # 'links': [link['href'] for link in entry.links[1:] if link['type'] == 'text/html']
        }

        logger.debug("Finished building document " + doc['documentID'])
        logger.debug(doc)
        return doc
