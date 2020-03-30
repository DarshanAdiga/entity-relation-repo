import spacy
import textacy
import en_core_web_sm
from spacy.pipeline import DependencyParser
from indexer import ESHelper
import csv
import json

class SentenceParser():
    def __init__(self):
        self.sp_core_nlp = en_core_web_sm.load()

    def fetch_from_es(self):
        """
        Fetch the articles from ES
        """
        es_helper = ESHelper()
        article_list = es_helper.search('{"query":{"bool":{"must":[{"match_all":{}}],"must_not":[],"should":[]}},"from":0,"size":10,"sort":[],"aggs":{}}')
        print('Fetched 10 documents. #TODO Need to implement pagination')
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

        # TODO Clean the sentences and create a new list of parsed sentences
        print('Tokenized {} sentences'.format(len(sentences)))
        return sentences
 
    def get_all_entities(self, parsed_sentence):
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
        
    def get_all_relations(self, parsed_sentence):
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

    def get_sub_verb_obj_triplets(self, p_sentence, row_dict):
        """
        Returns zero or more number of triplets each containing 
        (subject,verb,object) in the p_sentence.
        This method uses textacy(https://chartbeat-labs.github.io/textacy/build/html/index.html)
        
        Arguments:
            p_sentence {Doc} -- Parsed sentence
            row_dict {dict} -- result dictionary
        
        Returns:
            [dict] -- Dictionary with different parsed components of the sentence
        """
        itr = textacy.extract.subject_verb_object_triples(p_sentence)
        if itr is not None:
            svo = [val for val in itr]
            for i,item in enumerate(svo):
                i = str(i)
                s,v,o = item
                row_dict[i + '_sub'] = s.text
                row_dict[i + '_verb'] = v.text
                row_dict[i + '_obj'] = o.text

        return row_dict

    def parse(self, result_file_path):
        """
        Parses the article texts from ES and identifies the entities and relationships
        
        Arguments:
            result_file_path {str} -- Destination file path where the parsed result will be save as json lines
        """
        article_list = self.fetch_from_es()
        parsed_sentences = self.sentence_tokenizer_and_parser(article_list)

        # The result json line file
        f_write = open(result_file_path, 'w')
        # For each parsed sentence
        for p_sentence in parsed_sentences:
            row_dict = {}
            row_dict = self.get_sub_verb_obj_triplets(p_sentence, row_dict)
            entities = self.get_all_entities(p_sentence)
            relations = self.get_all_relations(p_sentence)
            
            if row_dict is not None:
                row_dict['text'] = p_sentence.text
                row_dict['entities'] = json.dumps(entities)
                row_dict['relations'] = json.dumps(relations)
                f_write.write(json.dumps(row_dict) + '\n')
        
        f_write.close()
        print('Saved the parsed results at {}'.format(result_file_path))

if __name__ == "__main__":
    sp = SentenceParser()
    sp.parse('data/parsed_data.jl')