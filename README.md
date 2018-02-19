# HackathonITAINNOVA
## Social Media Monitoring.

This repository contains the code developed by ITAINNOVA's group for the [II Hackathon on Human Language Technologies](http://www.hackathonplantl.es/).

The solution is composed of three main parts:

### NLP services
NLP core services developed over our platform [Moriarty](http://www.ita.es/moriarty/) and exposed via REST API.

### Crawlers
Data intake from Facebook, Twitter and RSS.
Published Python code gets user's social networks information, invokes NLP services and store results in Solr.

#### Python dependencies
* [facebook](https://github.com/mobolic/facebook-sdk)
* [tweepy](https://github.com/tweepy/tweepy)
* [feedparser](https://github.com/kurtmckee/feedparser)
* [pysolr](https://github.com/django-haystack/pysolr)

### WebApp
User interface.



##### You may find more information about our services at: [ITAINNOVA](http://www.itainnova.es), contacting with the **Big Data and Cognitive Systems** group (formerly **Software Engineering**). Don't hesitate to contact us!

