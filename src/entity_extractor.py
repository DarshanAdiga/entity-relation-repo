import spacy
import en_core_web_sm
from spacy.pipeline import DependencyParser
from indexer import ESHelper
import csv

sp_core_nlp = en_core_web_sm.load()

esh = ESHelper(rss_url_file='data/rss-urls.txt')
articel_list = esh.search('{"query":{"bool":{"must":[{"match_all":{}}],"must_not":[],"should":[]}},"from":0,"size":10,"sort":[],"aggs":{}}')
#print(articel_list)

# Save entities
ent_file = './data/sample_entities.csv'
ent_file = open(ent_file, 'w')
ent_writer = csv.DictWriter(ent_file, fieldnames=['token', 'label'])
ent_writer.writeheader()

# Save dependencies
dep_file = './data/sample_dependencies.csv'
dep_file = open(dep_file, 'w')
dep_writer = csv.DictWriter(dep_file, fieldnames=['token', 'dep'])
dep_writer.writeheader()

def write_deps(parsed_sent, dep_writer):
    for dp in parsed_sent:
        if (len(dp.text.strip()) > 1 and dp.text.strip() !='\n'):
            row = {}
            row['token'] = dp.text
            row['dep'] = dp.dep_ 
            dep_writer.writerow(row)

def write_ents(parsed_sent, ent_writer):
    for ent in parsed_sent.ents:
        if (len(ent.text.strip()) > 1 and ent.text.strip() !='\n'):
            row = {}
            row['token'] = ent.text.strip()
            row['label'] = ent.label_
            ent_writer.writerow(row)
        
for ar in articel_list:
    parsed_article = sp_core_nlp(ar['text'])
    for i,sent in enumerate(parsed_article.sents):
        #print(i,':',sent.text)
        #parsed_sent = sp_core_nlp(sent.text)
        write_deps(sent, dep_writer)
        write_ents(sent, ent_writer)

print('Saved entities and dependencies to file')