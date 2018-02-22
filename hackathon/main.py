from .crawlers import Facebook, Twitter, RSS
from .solr import Solr
from .call_WF import call_WF
from .multi import Pool

import time
from datetime import datetime

from . import config
import logging
logger = logging.getLogger(__name__)


facebook = Facebook()
twitter = Twitter()
rss = RSS()
solr = Solr()
pool = Pool()


def get_all_docs(from_fb, from_tw, from_rss):
    # Process all post from FACEBOOK
    if from_fb:
        try:
            logger.info("Starting Facebook crawling")
            fb_since = solr.get_facebook_last_date()
            fb_limit = 0 if fb_since else config.settings.FACEBOOK_INITIAL_LIMIT_PER_PAGE
            yield from facebook.get_all_docs(limit=fb_limit, since=fb_since)
            logger.info("Facebook crawling ended")
        except:
            logger.exception("FATAL ERROR, facebook crawling failed")

    # Process all tweets from TWITTER
    if from_tw:
        try:
            logger.info("Starting Twitter crawling")
            tw_since = solr.get_twitter_last_id()
            tw_limit = 0 if tw_since else config.settings.TWITTER_INITIAL_LIMIT
            yield from twitter.get_all_docs(limit=tw_limit, since_id=tw_since)
            logger.info("Twitter crawling ended")
        except:
            logger.exception("FATAL ERROR, twitter crawling failed")

    # Process all entries from RSSs
    if from_rss:
        try:
            logger.info("Starting RSS crawling")
            rss_since = solr.get_rss_last_date()
            rss_limit = 0 if rss_since else config.settings.RSS_INITIAL_LIMIT_PER_PAGE
            yield from rss.get_all_docs(limit=rss_limit, since=rss_since)
            logger.info("RSS crawling ended")
        except:
            logger.exception("FATAL ERROR, rss crawling failed")


def process_all_docs(from_fb=True, from_tw=True, from_rss=True):

    def parallel_task(document):
        logger.debug(document)
        response = call_WF(document['text'], document['textSentiment'])
        if response:
            document.update(response)
            logger.debug(document)
            solr.insert(document)
            logger.info("SUCCESS! Document {} inserted in solr".format(document['documentID']))
        else:
            logger.warning("FAIL! Document {} NOT inserted in solr".format(document['documentID']))

    pool.parallelize(parallel_task, get_all_docs(from_fb, from_tw, from_rss))


def periodic_task():
    INTERVAL = config.settings.MINUTES_BETWEEN_CALLS * 60
    next_task = time.time() + INTERVAL

    def sleep_until(unix_time):
        interval = unix_time - time.time()
        if interval > 0:
            time.sleep(interval)

    logger.info("Task starting")

    while True:
        try:
            process_all_docs()
        except:
            logger.exception("FATAL ERROR, process stopped")

        logger.info("Task going to sleep")
        logger.info("Next iteration: {}".format(datetime.fromtimestamp(next_task).ctime()))
        sleep_until(next_task)

        logger.info("Task awoken")
        next_task += INTERVAL
