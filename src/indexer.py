from elasticsearch import Elasticsearch
import json
import conf_parser
import rss_fetch

elastic_conf = conf_parser.SYS_CONFIG['elastic']
#print('Read config:', conf_parser.SYS_CONFIG)

class ESHelper():
    def __init__(self, rss_url_file):
        # Initialize the connection
        self.es = self._init_es()
        self.rss_url_file = rss_url_file
        self.index = elastic_conf['index']
        self.doc_type = elastic_conf['doc_type']

    def _init_es(self):
        """
        Initializes the elastic-search client and returns it
        """
        es = Elasticsearch([{'host': elastic_conf['host'], 'port': elastic_conf['port']}])
        print('Connected to Elastic Search:', es.ping())
        return es

    def index_news_articles(self):
        """
        Fetches and indexes the news articles from the rss feeds 
        """
        # Get the RSS feed
        print('Fetching the RSS feed')
        item_list = rss_fetch.get_all_feed_urls(self.rss_url_file)
        # Index all the feed items into ES
        print('Going to index {0} news articles...'.format(len(item_list)))
        drop_count=0
        for item in item_list:
            try:
                # Use item specific id while indexing to avoid duplication
                self.es.index(index=self.index, doc_type=self.doc_type, id=item['id'], body=item)
            except KeyError as e:
                drop_count += 1
                print(str(e))

        print('Indexed {0} Dropped {1}'.format(len(item_list)-drop_count, drop_count))
        print('Current index size {0}'.format(self.get_index_size()))

    def get_index_size(self):
        """
        Return the total number of docs present in the index
        """
        return self.es.indices.stats()['indices'][self.index]['total']['docs']['count']

    def article_by_id(self, id):
        """
        Get the article with the given id
        """
        return self.es.get(index=self.index, doc_type=self.doc_type, id=id)

    def search(self, json_query):
        """
        Search the index using given json_query and return the list of article objects
        """
        res = self.es.search(index=self.index, body=json_query)
        #print(json.dumps(res, indent=2))
        # Process the results and return the article objects only
        articel_list = [src['_source'] for src in res['hits']['hits']]
        return articel_list

if __name__ == "__main__":    
    # Fetch the feeds and index
    esh = ESHelper(rss_url_file='data/rss-urls.txt')
    esh.index_news_articles()