from .crawlers import Facebook, Twitter, RSS
from .solr import Solr
from .call_WF import call_WF2
import time

from . import config
import logging
logger = logging.getLogger(__name__)


facebook = Facebook()
twitter = Twitter()
solr = Solr()
rss = RSS()


def get_all_docs():
    # # Process all post from FACEBOOK
    # # limit => post per page
    logger.info("Starting Facebook crawling")
    fb_since = solr.get_facebook_last_date()
    fb_limit = 0 if fb_since else config.settings.FACEBOOK_INITIAL_LIMIT_PER_PAGE

    yield from facebook.get_all_docs(limit=fb_limit, since=fb_since)
    logger.info("Facebook crawling ended")

    # Process all tweets from TWITTER
    # limit => total tweets
    logger.info("Starting Twitter crawling")
    tw_since = solr.get_twitter_last_id()
    tw_since = None
    tw_limit = 0 if tw_since else config.settings.TWITTER_INITIAL_LIMIT

    yield from twitter.get_all_docs(limit=tw_limit, since_id=tw_since)
    logger.info("Twitter crawling ended")

    # Process all entries from RSSs
    logger.info("Starting RSS crawling")
    rss_since = solr.get_rss_last_date()
    rss_limit = 0 if rss_since else config.settings.RSS_INITIAL_LIMIT_PER_PAGE

    yield from rss.get_all_docs(limit=rss_limit, since=rss_since)
    logger.info("RSS crawling ended")


def process_all_docs():
    for document in get_all_docs():
        # response = {}
        # if True:
        response = call_WF2(document['text'])
        if response:
            document.update(response)
            logger.debug(document)
            solr.insert(document)
            logger.info("SUCCESS! Document {} inserted in solr".format(document['documentID']))
        else:
            logger.warning("FAIL! Document {} NOT inserted in solr".format(document['documentID']))


def periodic_task():
    INTERVAL = config.settings.MINUTES_BETWEEN_CALLS * 60
    next_task = time.time() + INTERVAL

    while True:
        process_all_docs()

        logger.info("Task going to sleep")
        time.sleep(next_task - time.time())

        logger.info("Task awoken")
        next_task += INTERVAL
