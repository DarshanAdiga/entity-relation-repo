from elasticsearch import Elasticsearch
import conf_parser

#print('Read config:', conf_parser.SYS_CONFIG)

elastic_conf = conf_parser.SYS_CONFIG['elastic']
es = Elasticsearch([{'host': elastic_conf['host'], 'port': elastic_conf['port']}])
print('Connected to Elastic Search:', es.ping())