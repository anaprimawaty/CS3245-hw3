from __future__ import division
import os
import getopt
import sys
import nltk
import pickle
import math
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.stem.porter import *


# Function that loops through each line in query file,
# performs query and writes result of query to output file
def search_index(dictionary_file, postings_file, queries_file, output_file):
    dictionary = pickle.load(open(dictionary_file, 'rb'))
    postings_list = open(postings_file, 'r')
    query_list = open(queries_file, 'r').read().split("\n")
    search_results = open(output_file, 'w')

    for index, query in enumerate(query_list):
        # in case blank line is caught as a query, write an empty line
        if query == "":
            search_results.write("\n")
        else:
            score_dict = get_scores(query, dictionary, postings_list)
            print score_dict
            # if index != len(query_list) - 1:
            #     search_results.write("\n")


def get_scores(query_str, dictionary, postings_list):
    total_doc_count = dictionary["DOCUMENT_COUNT"]
    doc_norm_factors = dictionary["DOCUMENT_NORM_FACTORS"]
    score_dict = {}
    # for computing final normalizing values
    query_norm_factor = 0
    query_dict = process_query(query_str)
    for term in query_dict:
        if term in dictionary:
            # query computations
            doc_freq = dictionary[term][0]
            idf = math.log10(total_doc_count / doc_freq)
            query_tf = 1 + math.log10(query_dict[term])
            query_wt = idf * query_tf
            query_norm_factor += math.pow(query_wt, 2)
            # retrieving postings list for term
            pointer = dictionary[term][1]
            posting_list = get_posting_list(doc_freq, pointer, postings_list)
            # document computations
            for posting in posting_list:
                doc_id = posting[0]
                doc_tf = 1 + math.log10(posting[1])
                score = doc_tf * query_wt
                if doc_id in score_dict:
                    score_dict[doc_id] += score
                else:
                    score_dict[doc_id] = score
    return normalize(score_dict, query_norm_factor, doc_norm_factors)


# Normalizes scoring dictionary
def normalize(score_dict, query_norm_factor, doc_norm_factors):
    query_norm_factor = math.pow(query_norm_factor, 0.5)
    # # query_norm_factor will be zero only if idf for all query terms are zero
    # # In this case we set idf to 1, to rely only on tf for scoring
    # if query_norm_factor == 0:
    #     query_norm_factor = 1
    for doc_id, score in score_dict.iteritems():
        norm_factor = doc_norm_factors[str(doc_id)] * query_norm_factor
        score_dict[doc_id] = score / norm_factor
    return score_dict


# Converts query string into dictionary form
def process_query(query_str):
    stemmer = PorterStemmer()
    query_list = query_str.split(" ")
    query_dict = {}
    for query in query_list:
        query = stemmer.stem(query).lower()
        if query in query_dict:
            query_dict[query] += 1
        else:
            query_dict[query] = 1
    return query_dict


# Function that seeks, loads and returns a posting list
def get_posting_list(freq, pointer, postings_list):
    postings_list.seek(pointer)
    results_list = postings_list.read(freq * 2 * 15 - 1).split(" ")
    results_list.pop()
    results_list = map((lambda x: int(x, 2)), results_list)
    tuple_list = []
    for i in range(0, len(results_list), 2):
        tuple_list.append((results_list[i], results_list[i + 1]))
    return tuple_list


# Function that converts list to string for writing to file
def stringify(list):
    ans = ""
    for element in list:
        ans += str(element) + " "
    return ans.strip()


def usage():
    print "usage: " + sys.argv[0] + " -d dictionary-file -p postings-file -q file-of-queries -o output-file-of-results"

input_file_d = input_file_p = input_file_q = output_file = None
try:
    opts, args = getopt.getopt(sys.argv[1:], 'd:p:q:o:')
except getopt.GetoptError, err:
    usage()
    sys.exit(2)
for o, a in opts:
    if o == '-d':
        input_file_d = a
    elif o == '-p':
        input_file_p = a
    elif o == '-q':
        input_file_q = a
    elif o == '-o':
        output_file = a
    else:
        assert False, "unhandled option"
if input_file_d is None or input_file_p is None or input_file_q is None or output_file is None:
    usage()
    sys.exit(2)


search_index(input_file_d, input_file_p, input_file_q, output_file)
