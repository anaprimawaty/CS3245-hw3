import sys
import getopt
import os
import math
import pickle
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.stem.porter import *


# Takes in a path string and outputs a list of file names in the directory
def get_doc_names(path):
    doc_names = os.listdir(path)
    doc_names = map(int, doc_names)
    doc_names.sort()
    doc_names = map(str, doc_names)
    return doc_names


def write_dictionary(dictionary, dictionary_file):
    pickle.dump(dictionary, dictionary_file)


def write_postings(dictionary, postings_lists, postings_file):
    for term in dictionary:
        file_pointer = postings_file.tell()
        df = dictionary[term][0]
        term_pointer = dictionary[term][1]
        postings_list = postings_lists[term_pointer]
        for posting in postings_list:
            postings_file.write(convert_to_bytes(posting[0]) + " ")
            postings_file.write(convert_to_bytes(posting[1]) + " ")
        dictionary[term] = (df, file_pointer)
    return dictionary


def convert_to_bytes(num):
    return '{0:014b}'.format(int(num))


def build_index(input_doc_path, output_file_d, output_file_p):
    dictionary_file = open(output_file_d, 'wb')
    postings_file = open(output_file_p, 'w')

    stemmer = PorterStemmer()
    # main_dict stores key = term, value = (df, pointer to postings)
    main_dict = {}
    # postings_lists stores key = pointer, value = array of (doc name, tf)
    postings_lists = {}
    # doc_norm_factors stores key = doc name, value = normalising factor (length)
    doc_norm_factors = {}

    doc_names = get_doc_names(input_doc_path)

    for doc_name in doc_names:
        doc = open(input_doc_path + '/' + doc_name, 'r').read()
        # doc_dict stores key = term, value = tf for current doc
        doc_dict = {}
        # doc_norm_factor stores normalising factor (length) for current doc
        doc_norm_factor = 0

        for sentence in sent_tokenize(doc):
            for word in word_tokenize(sentence):
                token = stemmer.stem(word).lower()
                # updating of term frequency
                if token in doc_dict:
                    doc_dict[token] += 1
                else:
                    doc_dict[token] = 1

        for term, term_freq in doc_dict.iteritems():
            doc_wt = 1 + math.log10(term_freq)
            doc_norm_factor += math.pow(doc_wt, 2)
            if term not in main_dict:
                term_pointer = len(postings_lists)
                main_dict[term] = (1, term_pointer)
                postings_lists[term_pointer] = [(doc_name, term_freq)]
            else:
                df = main_dict[term][0]
                term_pointer = main_dict[term][1]
                main_dict[term] = (df + 1, term_pointer)
                postings_lists[term_pointer].append((doc_name, term_freq))

        doc_norm_factors[doc_name] = math.pow(doc_norm_factor, 0.5)

    main_dict = write_postings(main_dict, postings_lists, postings_file)
    main_dict["DOCUMENT_COUNT"] = len(doc_names)
    main_dict["DOCUMENT_NORM_FACTORS"] = doc_norm_factors
    write_dictionary(main_dict, dictionary_file)
    dictionary_file.close()
    postings_file.close()


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
