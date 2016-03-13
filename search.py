import os
import getopt
import sys
import nltk
import pickle
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.stem.porter import *
from sets import Set
from shunting_yard import *
from merge import *


# Function that loops through each line in query file,
# performs query and writes result of query to output file
def search_index(dictionary_file, postings_file, queries_file, output_file):
    dictionary = pickle.load(open(dictionary_file, 'rb'))
    postings_list = open(postings_file, 'r')
    query_list = open(queries_file, 'r').read().split("\n")
    search_results = open(output_file, 'w')

    for index, query in enumerate(query_list):
        # in case blank line is caught as a query, write an empty line
        if query != "":
            query_obj = get_query_obj(query, dictionary)
            output_list = process_query_obj(query_obj, dictionary, postings_list)
            search_results.write(stringify(output_list))
            if index != len(query_list) - 1:
                search_results.write("\n")
        else:
            search_results.write("\n")


# Function that takes in Query object, dictionary and postings lists
# to output result of query
# by recursively unwrapping Query objects and performing merges 
# until base case of Word object is reached
def process_query_obj(query_obj, dictionary, postings_list):
    all_doc_ids = dictionary["ALL_TERMS"]

    if isinstance(query_obj, Word):
        term = query_obj.value
        if term in dictionary:
            freq = dictionary[term][0]
            pointer = dictionary[term][1]
            posting_list = get_posting_list(freq, pointer, postings_list)
            if query_obj.is_not:
                posting_list = negate(posting_list, all_doc_ids)
            return posting_list
        elif query_obj.is_not:
            return all_doc_ids
        else:
            return []

    elif isinstance(query_obj, Query):
        posting_list1 = process_query_obj(query_obj.value1, dictionary, postings_list)
        posting_list2 = process_query_obj(query_obj.value2, dictionary, postings_list)
        results_list = merge(posting_list1, posting_list2, query_obj.op)
        if query_obj.is_not:
            results_list = negate(results_list, all_doc_ids)
        return results_list


# Function that seeks, loads and returns a posting list
def get_posting_list(freq, pointer, postings_list):
    postings_list.seek(pointer)
    results_list = postings_list.read(freq * 15 - 1).split(" ")
    results_list.pop()
    results_list = map((lambda x: int(x, 2)), results_list)
    return results_list


# Function that outputs a list with elements present in list2 but not in list1
def negate(list1, list2):
    result = []
    ptr1 = 0
    ptr2 = 0
    while ptr1 < len(list1) and ptr2 < len(list2):
        if list1[ptr1] == list2[ptr2]:
            ptr1 += 1
            ptr2 += 1
        elif list1[ptr1] > list2[ptr2]:
            result.append(list2[ptr2])
            ptr2 += 1
        else:
            ptr1 += 1
    while (ptr2 < len(list2)):
            result.append(list2[ptr2])
            ptr2 += 1
    return result


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
