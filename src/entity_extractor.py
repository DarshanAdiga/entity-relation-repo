import spacy
import en_core_web_sm
from indexer import ESHelper

sp_core_nlp = en_core_web_sm.load()

esh = ESHelper(rss_url_file='data/rss-urls.txt')
articel_list = esh.search('{"query":{"bool":{"must":[{"match_all":{}}],"must_not":[],"should":[]}},"from":0,"size":10,"sort":[],"aggs":{}}')
#print(articel_list)

res_csv = []
for ar in articel_list:
    parsed = sp_core_nlp(ar['text'])
    ents = [ent for ent in parsed.ents ]
    ents = [ent for ent in ents if (len(ent.text.strip()) > 1 and ent.text.strip() !='\n')]
    res_csv.extend([ent.text.strip() + ',' + ent.label_ for ent in ents])

# Save to file
with open('/home/darshan/work/ML/stock-market/entity-relation-repo/data/sample_entities.csv', 'w') as ot:
    for r in res_csv:
        #print(r, ':', len(r))
        ot.write(r + "\n")
print('Saved {} entities to file'.format(len(res_csv)))
