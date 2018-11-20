import feedparser
import json
import requests
from bs4 import BeautifulSoup

def get_all_feed_urls(file_path):
    """
    Get rss feed(list of json objects with title, url, text and published fields) 
    of all the urls present in the given file_path
    """
    all_news_articles = []
    with open(file_path, 'r') as in_file:
        for rss_url in in_file:
            all_news_articles.extend(get_feeds(rss_url))
    
    print('Fetched {0} news articles'.format(len(all_news_articles)))
    return all_news_articles

def get_feeds(rss_url, verbose=False):
    """
    Fetches the rss feed from the given url and parses the feed into a list of json objects
    with title, url, text and published fields
    """
    feed = feedparser.parse(rss_url)
    ##print(json.dumps(feed, indent=2))
    item_json_list = []
    for item in feed.entries:
        article_text = extract_article_text(item.link)
        i_json = json.loads('{}')
        i_json['id'] = find_article_id(item)
        i_json['title'] = item.title
        i_json['url'] = item.link
        i_json['text'] = article_text
        i_json['published'] = item.published
        if verbose:
            print(json.dumps(i_json)) 
            print('------------------------------------')
        item_json_list.append(i_json)
    
    return item_json_list
        

def find_article_id(item):
    """
    Find and return the article id
    """
    if item.id and len(item.id) > 0:
        try:
            # Return the last word in the id. Check the sample rss feed to know more
            return item.id.split()[-1]
        except KeyError as e:
            print(str(e))
    # In case of errors, use the link itself as id
    return item.link


def extract_article_text(article_link):
    """
    Extracts and returns the text from the given article_link using a fixed XPATH
    TODO: Make this a generic method
    """
    res = requests.get(article_link)  
    if res.status_code == 200:
        soup = BeautifulSoup(res.text, 'html.parser')
        #print(soup.prettify())
        #XPATH For the first article's text 
        #/html/body/section[2]/div[6]/div/div/section/div[1]/article/div[5]
        article_text = soup.find('body').find_all('section')[1] \
        .find_all('article')[0] \
        .find_all('div', class_='artText')[0].get_text()

        return article_text
    else:
        return none

if __name__ == '__main__':
    item_list = get_feeds('https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms')
    for it in item_list:
        print(it)
    #get_all_feed_urls('data/rss-urls.txt')
