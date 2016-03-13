import os
import getopt
import sys
import nltk
import math
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.stem.porter import *
import pickle


# Function that takes in a path string
# and outputs a list of file names at the directory
def get_doc_names(path):
    doc_names = os.listdir(path)
    doc_names = map(int, doc_names)
    doc_names.sort()
    doc_names = map(str, doc_names)
    return doc_names


def write_dictionary(dictionary, dictionary_file):
    pickle.dump(dictionary, dictionary_file)


def write_postings(dictionary, postings, postings_file):
    for term in dictionary:
        file_pointer = postings_file.tell() + 1
        freq = dictionary[term][0]
        list_pointer = dictionary[term][1]
        postings_list = postings[list_pointer]
        for posting in postings_list:
            postings_file.write(convert_to_bytes(posting[0]) + " ")
            postings_file.write(convert_to_bytes(posting[1]) + " ")
        dictionary[term] = (freq, file_pointer)
    return dictionary


def convert_to_bytes(num):
    return '{0:014b}'.format(int(num))


def build_index(input_doc_path, output_file_d, output_file_p):
    dictionary_file = open(output_file_d, 'wb')
    postings_file = open(output_file_p, 'w')

    stemmer = PorterStemmer()
    dictionary = {}
    postings = {}
    doc_norm_factors = {}

    doc_names = get_doc_names(input_doc_path)

    for doc_name in doc_names:
        doc = open(input_doc_path + '/' + doc_name, 'r').read()
        doc_dictionary = {}
        norm_factor = 0
        for sentence in sent_tokenize(doc):
            for word in word_tokenize(sentence):
                token = stemmer.stem(word).lower()
                if token in doc_dictionary:
                    doc_dictionary[token] += 1
                else:
                    doc_dictionary[token] = 1
        for term, term_freq in doc_dictionary.iteritems():
            doc_tf = 1 + math.log10(term_freq)
            norm_factor += math.pow(doc_tf, 2)
            if term not in dictionary:
                dictionary[term] = (1, len(postings))
                term_frequency = doc_dictionary[term]
                postings[len(postings)] = [(doc_name, term_frequency)]
            else:
                freq = dictionary[term][0]
                pointer = dictionary[term][1]
                dictionary[term] = (freq + 1, pointer)
                postings[pointer].append((doc_name, term_frequency))
        doc_norm_factors[doc_name] = math.pow(norm_factor, 0.5)
    dictionary = write_postings(dictionary, postings, postings_file)
    dictionary["DOCUMENT_COUNT"] = len(doc_names)
    dictionary["DOCUMENT_NORM_FACTORS"] = doc_norm_factors
    write_dictionary(dictionary, dictionary_file)


def usage():
    print "usage: " + sys.argv[0] + " -i directory-of-documents -d dictionary-file -p postings-file"

input_doc_path = output_file_d = output_file_p = None
try:
    opts, args = getopt.getopt(sys.argv[1:], 'i:d:p:')
except getopt.GetoptError, err:
    usage()
    sys.exit(2)
for o, a in opts:
    if o == '-i':
        input_doc_path = a
    elif o == '-d':
        output_file_d = a
    elif o == '-p':
        output_file_p = a
    else:
        assert False, "unhandled option"
if input_doc_path is None or output_file_d is None or output_file_p is None:
    usage()
    sys.exit(2)


build_index(input_doc_path, output_file_d, output_file_p)
