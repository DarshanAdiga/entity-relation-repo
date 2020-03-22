# Entity Relationship Management

A work-in-progress project aimed at building a entity-relationship builder system using natural language processing techniques and machine learning algorithms



## Goals of the project (For reference)

- Identify the entities from various data sources like news, blogs etc
- Identify the relationship and categorical scores and sentiments
- Build a historical knowledge graph of entities and various scores
- Analyse how entities are related, how the sentiment varies over a period of time
- Predict/forecast the futuristic sentiment and categorical scores

## easticsearch Container Setup
The elasticsearch docker container version `7.6.1` is used. More details: https://hub.docker.com/_/elasticsearch/

Start the elastic search container using
```bash
docker run -d --name elasticsearch -p 9200:9200 -p 9300:9300 -e "discovery.type=single-node" elasticsearch:7.6.1
```

## Components
**indexer.py**: Index the newly available news articles into elasticsearch


