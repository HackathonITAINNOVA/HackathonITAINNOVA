
# HackathonITAINNOVA
## Social Media Monitoring.
Installation instructions:

### NLP services
[Moriarty](www.ita.es/moriarty) platform is needed in order to provide NLP services exposed as REST services.

### Crawlers
Install Python in your machine (both, Python 2.x and Python 3.x are compatible).

We strongly recommend using virtual environments.

#### Python dependencies
* [facebook-sdk](https://github.com/mobolic/facebook-sdk) 
* [tweepy](https://github.com/tweepy/tweepy)
* [feedparser](https://github.com/kurtmckee/feedparser)
* [pysolr](https://github.com/django-haystack/pysolr)
* [beautiful soup](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)

Execute [run.py](run.py), it will launch a periodic task that will crawl information from social networks.

You will need a 'private.py' configuration file at ./config directory to store api keys, nlp services and solr urls.

### Solr
[Apache Solr](http://lucene.apache.org/solr/) is needed in order to store processing results. We are currently using 6.5.0 version in standalone mode.

### WebApp
Download source code and install it on your web applications server.

&nbsp;

Currently... *Dockerizing*