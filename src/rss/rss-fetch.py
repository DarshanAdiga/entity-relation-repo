import feedparser
import json
import requests
from bs4 import BeautifulSoup

def get_all_feed_urls(file_path):
    with open(file_path, 'r') as in_file:
        for rss_url in in_file:
            get_feeds(rss_url)

def get_feeds(rss_url):
    feed = feedparser.parse(rss_url)
    #print(json.dumps(feed, indent=2))
    for item in feed.entries:
        print('title:', item.title) 
        print('url:', item.link) 
        print('text:', extract_article_text(item.link))
        print('published:', item.published) 
        print('------------------------------------')

def extract_article_text(article_link):
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
    get_feeds('https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms')
    #get_all_feed_urls('data/rss-urls.txt')
