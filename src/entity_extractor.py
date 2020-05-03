import spacy
import textacy
import en_core_web_sm
from spacy.pipeline import DependencyParser
from indexer import ESHelper
import csv
import json
import traceback
from deprecation import deprecated

class SentenceParser():
    def __init__(self):
        self.sp_core_nlp = en_core_web_sm.load()
        self.VERB_PHRASE_REGEX = r'(<AUX>*<VERB>?[<ADP><PART><ADV>]*<VERB>+<ADP>?)'

    def fetch_from_es(self):
        """
        Fetch the articles from ES
        """
        es_helper = ESHelper()
        article_list = es_helper.search('{"query":{"bool":{"must":[{"match_all":{}}],"must_not":[],"should":[]}},"from":0,"size":10,"sort":[],"aggs":{}}')
        print('Fetched {} documents. #TODO Need to implement pagination'.format(len(article_list)))
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

    @deprecated()
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

    @deprecated()
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

    def comes_before(self, tok1, tok2):
        #print(tok1, ',', tok2)
        return tok1.start < tok2.start

    def get_node_edge_pairs(self, doc, verb_phrases, noun_chunks):
        """Identifies (noun_chunk,verb,noun_chunk) tripletes in the given doc
        and returns a list of triplets
        
        Arguments:
            doc {Doc} -- Parsed sentence documnet
            verb_phrases {List} -- List of spans representing verb phrases
            noun_chunks {List} -- List of spans representing noun chunks
        
        Returns:
            List -- List of (noun,verb,noun) triplets
        """
        # If either of the lists are empty, nothing to do here
        if len(verb_phrases) == 0 or len(noun_chunks) == 0:
            return None

        vp_i = nc_i = 0
        node_edge_node_list = []
        start_node = end_node = edge = None
        while True:
            # If still both the lists have unseen tokens
            if vp_i < len(verb_phrases) and nc_i < len(noun_chunks):
                if self.comes_before(verb_phrases[vp_i], noun_chunks[nc_i]):
                    start_tok = verb_phrases[vp_i]  
                    visited = False
                    while(vp_i < len(verb_phrases) and self.comes_before(verb_phrases[vp_i], noun_chunks[nc_i])):
                        vp_i += 1
                        visited = True

                    # Update vp_i if it had entered the loop
                    if visited:
                        vp_i -= 1
                    end_tok = verb_phrases[vp_i]
                    
                    # Mark this as edge
                    edge = doc[start_tok.start:end_tok.end]
                    # Move to next verb phrase
                    vp_i += 1

                else:
                    start_tok = noun_chunks[nc_i]
                    visited = False
                    while(nc_i < len(noun_chunks) and self.comes_before(noun_chunks[nc_i], verb_phrases[vp_i])):
                        nc_i += 1
                        visited = True

                    # Update nc_i if it had entered the loop
                    if visited:
                        nc_i -= 1   
                    end_tok = noun_chunks[nc_i]

                    # Identify the start node, edge and end node
                    if start_node == None:
                        start_node = doc[start_tok.start:end_tok.end]
                    else:
                        end_node = doc[start_tok.start:end_tok.end]
                        if edge != None:
                            # Found a node-edge-node triple here, reset the markers
                            node_edge_node_list.append((start_node, edge, end_node))
                            start_node = end_node
                            edge = None
                        else:
                            print('Triplet list so far:{}'.format(node_edge_node_list))
                            print('Something wrong! edge_node is not set {}'.format(doc))
                            print('start_node {} end_node {}'.format(start_node, end_node))
                    # Move to next noun chunk
                    nc_i += 1

                # End of inner if-else
            else:
                # If either of the list has been consumed
                if vp_i == len(verb_phrases):
                    # Verb phrases have been consumed, noun chuncks are available
                    # Remaining noun chunks will be the end_node if edge is already set
                    end_node = doc[noun_chunks[nc_i].start:]
                    if edge != None:
                        # Found a node-edge-node triple here, reset the markers
                        node_edge_node_list.append((start_node, edge, end_node))
                        start_node = end_node
                        edge = None
                    break
                else:
                    # Noun chuncks have been consumed, verb phrases are available
                    #print('Not sure what to do with un-used VB: {}'.format(verb_phrases[vp_i:]))
                    # Create an edge using the first un-used verb phrase
                    unused_vp = verb_phrases[vp_i]
                    edge = doc[unused_vp.start:unused_vp.end]
                    
                    # Create a dummy end node
                    end_node = None
                    # Create and add a triplet
                    node_edge_node_list.append((start_node, edge, end_node))
                    start_node = end_node
                    edge = None
                    
                    break
        # End of while loop
        #print('Triplets:', node_edge_node_list)
        return node_edge_node_list

    def get_truncated_noun_chunks(self, noun_chunks, verb_phrases):
        """Identify the noun chunks and verb phrases starting with the same token,
        truncate the noun chunk tokens until they don't have any common-starting-token.
        
        Arguments:
            noun_chunks {List} -- List of spans
            verb_phrases {List} -- List of spans
        
        Returns:
            List -- List of truncated noun chunks
        """
        # Identify if there is any overlap between noun chunks and verb phrases
        truncated_noun_chunks = {}
        for i,nc_vp in enumerate(zip(noun_chunks, verb_phrases)):
            nc,vp = nc_vp
            if nc.start == vp.start:
                while len(nc) > 0 and len(vp) > 0 and nc.start == vp.start:
                    nc = nc[1:]
                    vp = vp[1:]
                truncated_noun_chunks[i] = nc

        # Replace with the truncated noun_chunk
        for ind,nc in truncated_noun_chunks.items():
            noun_chunks[ind] = nc
        # Identify the empty noun chunks and drop them
        noun_chunks = [nc for nc in noun_chunks if len(nc) > 0]
        return noun_chunks
        
    def get_nvn_triplets(self, p_sentence, row_dict):
        """Returns dictionary containing noun-verb-noun objects for the given parsed sentence
        
        Arguments:
            p_sentence {Doc} -- Parsed sentence
            row_dict {Dict} -- Dict containing noun-verb-noun triplets
        """
        verb_phrases = list(textacy.extract.pos_regex_matches(p_sentence, self.VERB_PHRASE_REGEX))
        noun_chunks = list(p_sentence.noun_chunks)
        # print(p_sentence)
        # print('NC:', noun_chunks)
        # print('VP:', verb_phrases)
        noun_chunks = self.get_truncated_noun_chunks(noun_chunks, verb_phrases)
        # print('Truncated_NC:', noun_chunks)
        node_edge_node_list = self.get_node_edge_pairs(p_sentence, verb_phrases, noun_chunks)
        if node_edge_node_list is not None:
            for i,nvn in enumerate(node_edge_node_list):
                n1,v,n2 = nvn
                pre = str(i) + '_'
                row_dict[pre + 'noun1'] = n1.text
                row_dict[pre + 'verb'] = v.text
                row_dict[pre + 'noun2'] = n2.text if n2 is not None else None

        return row_dict

    def parse_2(self, result_file_path):
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
            row_dict = self.get_nvn_triplets(p_sentence, row_dict)
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
    sp.parse_2('data/parsed_data_vp.jl')