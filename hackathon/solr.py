import pysolr
# import pysolr.SolrError
from . import config


import logging
logger = logging.getLogger(__name__)


class Solr(object):
    URI = config.private.SOLR_URL + config.private.SOLR_COLLECTION

    def __init__(self):
        self.solr = pysolr.Solr(self.URI, timeout=10)

    def delete_all(self):
        logger.warning("Deleting all documents from solr")
        self.solr.delete(q='*:*')

    def delete_twitter(self):
        self.solr.delete(q='collectorID:twitter')

    def delete_facebook(self):
        self.solr.delete(q='collectorID:facebook')

    def delete_rss(self):
        self.solr.delete(q='collectorID:rss')

    def show_all(self):
        query = self.solr.search(q='*:*', rows=100000)
        for q in query:
            print(q)

    def insert(self, doc):
        doc["date"] = "NOW"
        try:
            self.solr.add([doc])
        except pysolr.SolrError:
            logger.exception("Insertion failed")

    def get_last_value(self, query, value):
        search = self.solr.search(q=query, sort=value + ' desc', fl=value, rows=1)
        if search.hits:
            return list(search)[0][value]

    def get_facebook_last_date(self):
        last_date = self.get_last_value('collectorID:facebook', 'date')
        logger.info("Facebook last date in solr: {}".format(last_date))
        return last_date

    def get_twitter_last_id(self):
        last_id = self.get_last_value('collectorID:twitter', 'postID')
        logger.info("Twitter last id in solr: {}".format(last_id))
        return last_id

    def get_rss_last_date(self):
        last_date = self.get_last_value('collectorID:rss', 'date')
        logger.info("RSS last date in solr: {}".format(last_date))
        return last_date
