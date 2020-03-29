import spacy
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
            entities = self.get_all_entities(p_sentence)
            relations = self.get_all_relations(p_sentence)
            rel_dict = self.get_merged_relations(p_sentence)
            if rel_dict is not None:
                rel_dict['text'] = p_sentence.text
                rel_dict['entities'] = json.dumps(entities)
                rel_dict['relations'] = json.dumps(relations)
                f_write.write(json.dumps(rel_dict) + '\n')
        
        f_write.close()
        print('Saved the parsed results at {}'.format(result_file_path))

    def get_merged_relations(self, parsed_sentence):
        """
        Iterates through the list of tokens from the parsed sentence and 
        returns the grouped subject-object relationships as a dictionary
        
        For more details on merging dependencies: https://www.analyticsvidhya.com/blog/2019/10/how-to-build-knowledge-graph-text-using-spacy/
        
        Arguments:
            parsed_sentence {Span} -- Spacy parsed sentence object
        """
        sub_token_text = ''
        obj_token_text = ''

        prev_tok_dep = '' # dependency tag of the previous token in the sentence
        prev_tok_text = '' # text of the previous token in the sentence

        prefix = ''
        modifier = ''
        for token in parsed_sentence:
            # if token is a punctuation mark then move on to the next token
            if token.dep_ != "punct":
                # check if the token is a compound word or not
                if token.dep_ == "compound":
                    prefix = token.text # Save this compound word as the prefix
                    # if the previous word was also a 'compound' then add the current word to it
                    if prev_tok_dep == "compound":
                        prefix = prev_tok_text + " " + token.text
                
                # check: token is a modifier or not
                if token.dep_.endswith("mod") == True:
                    modifier = token.text
                    # if the previous word was also a 'compound' then add the current word to it
                    if prev_tok_dep == "compound":
                        modifier = prev_tok_text + " " + token.text
                 
                # If the current token is a subject token, group the neighbouring tokens as well, if exists
                # and reset the prefix and modifier tokens
                if token.dep_.find("subj") == True:
                    sub_token_text = modifier + " " + prefix + " " + token.text
                    prefix = ""
                    modifier = ""
                    prev_tok_dep = ""
                    prev_tok_text = ""
                
                # If the current token is an object token, group the neighbouring tokens as well, if exists
                if token.dep_.find("obj") == True:
                    obj_token_text = modifier + " " + prefix + " " + token.text

                # finally set the previous token and text and then move on to next
                prev_tok_dep = token.dep_
                prev_tok_text = token.text

        # Return the parsed texts
        if sub_token_text == '' and obj_token_text == '':
            return None
        else: 
            return {'subject': sub_token_text, 'object': obj_token_text}

if __name__ == "__main__":
    sp = SentenceParser()
    sp.parse('data/parsed_data.jl')