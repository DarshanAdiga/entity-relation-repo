import spacy
import en_core_web_sm
from spacy.pipeline import DependencyParser
from indexer import ESHelper
import csv

class SentenceParser():
    def __init__(self):
        self.sp_core_nlp = en_core_web_sm.load()

    def fetch_from_es(self):
        """
        Fetch the articles from ES
        """
        es_helper = ESHelper()
        article_list = es_helper.search('{"query":{"bool":{"must":[{"match_all":{}}],"must_not":[],"should":[]}},"from":0,"size":10,"sort":[],"aggs":{}}')
        return article_list

    def sentence_tokenizer_and_parser(self, article_list):
        """
        Tokenize each article into parsed sentences
        
        Arguments:
            article_list {List} -- List of plain texts
        """
        sentences = []
        for article in article_list:
            article_text = article['text']
            parsed_article = self.sp_core_nlp(article_text)
            sentences.extend(parsed_article.sents)
        print('Tokenized {} sentences'.format(len(sentences)))
        return sentences
 
    def get_entities(self, parsed_sentence):
        """ Produces list of dicts from the parsed sentence, each dict containing
        the entities in a sentence.
        
        Arguments:
            parsed_sentence {Span} -- Parsed sentence
        """
        entities = []
        for ent in parsed_sentence.ents:
            # Filter the empty tokens
            if (len(ent.text.strip()) > 1 and ent.text.strip() !='\n'):
                row = {}
                row['token'] = ent.text.strip()
                row['label'] = ent.label_
                entities.append(row)
        return entities
        
    def get_relations(self, parsed_sentence):
        """ Produces list of dicts from the parsed sentence, each dict containing
        the relationships in a sentence.
        
        Arguments:
            parsed_sentence {Span} -- Parsed sentence
        """
        relations = []
        for dp in parsed_sentence:
            # Filter the empty tokens
            if (len(dp.text.strip()) > 1 and dp.text.strip() !='\n'):
                row = {}
                row['token'] = dp.text
                row['dep'] = dp.dep_
                relations.append(row)
        return relations

    def parse(self):
        article_list = self.fetch_from_es()
        parsed_sentences = self.sentence_tokenizer_and_parser(article_list)
        ent_list = []
        rel_list = []
        # For each parsed sentence
        for p_sentence in parsed_sentences:
            entities = self.get_entities(p_sentence)
            relations = self.get_relations(p_sentence)

            ent_list.extend(entities)
            rel_list.extend(relations)
        # TODO Save the parsed entities and relations
        print(ent_list)
        print()
        print(rel_list)

if __name__ == "__main__":
    sp = SentenceParser()
    sp.parse()