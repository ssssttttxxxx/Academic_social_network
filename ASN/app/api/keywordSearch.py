# coding=utf-8
import sys

from sklearn import feature_extraction
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.feature_extraction.text import CountVectorizer

from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, RegexpTokenizer

from gensim import corpora
from gensim.summarization import bm25
import os
import re

import string
reload(sys)
sys.setdefaultencoding("utf-8")


import MySQLdb
import pymongo

class KeywordSearch():

    def __init__(self,expert_name=None, paper_id=None):
        # self.db = MySQLdb.connect(host="localhost", user="root",passwd="stx11stx11", db="dblp_ref")
        self.client = pymongo.MongoClient('localhost', 27017)
        self.mongdb = self.client.Paper
        self.my_set = self.mongdb.Citation_total
        self.expert_name = expert_name
        self.paper_id = paper_id

    def searchProcess(self, enter_words, results):
        tokenizer = RegexpTokenizer(r'\w+')
        stop_words = stopwords.words('english')

        keywords = word_tokenize(enter_words)
        print keywords

        word_list = list()
        sorce = {}
        for word in keywords:
            word_list.append(re.compile(word))

        corpus = list()
        # 多条件查询
        # results = self.my_set.find({'title': {'$in': word_list}})
        # print results
        for i, result in enumerate(results):
            # print result['title']
            # print i

            # title_abstract = result['title']+': ' + result['abstract']
            title_abstract = result['title']
            title_abstract_tokenized = tokenizer.tokenize(title_abstract)
            # print title_abstract_tokenized
            title_abstract_tokenized = [w for w in title_abstract_tokenized if w not in stop_words]
            # print title_abstract_tokenized
            corpus.append(title_abstract_tokenized)

        dictionary_paper = corpora.Dictionary(corpus)
        print len(dictionary_paper)

        # doc_vectors = [dictionary_paper.doc2bow(text) for text in corpus]
        # vec1 = doc_vectors[0]
        # vec1_sorted = sorted(vec1, key=lambda (x, y): y, reverse=True)
        # print len(vec1_sorted)
        # for term, freq in vec1_sorted[:5]:
        #     print dictionary_paper[term]

        bm25Model = bm25.BM25(corpus)
        # 计算平均逆文档频率
        average_idf = sum(map(lambda k: float(bm25Model.idf[k]), bm25Model.idf.keys())) / len(bm25Model.idf.keys())

        enter_words_list = []
        for word in enter_words.strip().split():
            enter_words_list.append(word)
        scores = bm25Model.get_scores(enter_words_list, average_idf)
        # scores.sort(reverse=True)
        # print scores
        # idx = scores .index(max(scores))
        # print idx

        scores_index = list()
        for i, score in enumerate(scores):
            scores_index.append((i, score))
        scores_index.sort(key=lambda x:x[1], reverse=True)
        # print scores_index

        max_index= list()
        for i, score in scores_index:
            max_index.append(i)
        # print max_index
        return max_index

if __name__ == "__main__":
    KS = KeywordSearch()
    KS.searchProcess('health care')
