from .crawlers import Facebook, Twitter, RSS
from .solr import Solr
from .call_WF import call_WF
import time
from datetime import datetime
from multiprocessing.dummy import Pool as ThreadPool

from . import config
import logging
logger = logging.getLogger(__name__)


facebook = Facebook()
twitter = Twitter()
solr = Solr()
rss = RSS()


def get_all_docs(from_fb, from_tw, from_rss):
    # Process all post from FACEBOOK
    if from_fb:
        logger.info("Starting Facebook crawling")
        fb_since = solr.get_facebook_last_date()
        fb_limit = 0 if fb_since else config.settings.FACEBOOK_INITIAL_LIMIT_PER_PAGE
        yield from facebook.get_all_docs(limit=fb_limit, since=fb_since)
        logger.info("Facebook crawling ended")

    # Process all tweets from TWITTER
    if from_tw:
        logger.info("Starting Twitter crawling")
        tw_since = solr.get_twitter_last_id()
        tw_limit = 0 if tw_since else config.settings.TWITTER_INITIAL_LIMIT
        yield from twitter.get_all_docs(limit=tw_limit, since_id=tw_since)
        logger.info("Twitter crawling ended")

    # Process all entries from RSSs
    if from_rss:
        logger.info("Starting RSS crawling")
        rss_since = solr.get_rss_last_date()
        rss_limit = 0 if rss_since else config.settings.RSS_INITIAL_LIMIT_PER_PAGE
        yield from rss.get_all_docs(limit=rss_limit, since=rss_since)
        logger.info("RSS crawling ended")


def parallel_task(document):
    response = call_WF(document['text'])
    if response:
        document.update(response)
        logger.debug(document)
        solr.insert(document)
        logger.info("SUCCESS! Document {} inserted in solr".format(document['documentID']))
    else:
        logger.warning("FAIL! Document {} NOT inserted in solr".format(document['documentID']))


def process_all_docs(from_fb=True, from_tw=True, from_rss=True):
    pool = ThreadPool(config.settings.NUM_CONCURRENT_WORKERS)
    # imap uses correctly the generator, is more memory efficient
    pool.imap_unordered(parallel_task, get_all_docs(from_fb, from_tw, from_rss))
    pool.close()
    pool.join()


def sleep_until(unix_time):
    interval = unix_time - time.time()
    if interval > 0:
        time.sleep(interval)


def periodic_task():
    INTERVAL = config.settings.MINUTES_BETWEEN_CALLS * 60
    next_task = time.time() + INTERVAL
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
