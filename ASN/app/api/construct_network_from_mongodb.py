# -*- coding:utf-8 -*-
import pymongo
import MySQLdb
import networkx as nx
import matplotlib.pyplot as plt
import logging
import time
import sys

reload(sys)
sys.setdefaultencoding("utf-8")


class ConstructCitationTree():

    def __init__(self, paper_id):
        self.Graph = nx.DiGraph()
        self.client = pymongo.MongoClient('localhost', 27017)
        self.mongdb = self.client.Paper
        self.my_set = self.mongdb.Citation_added_title_year
        # self.my_set = self.mongdb.Citation
        self.paper_id = paper_id


    def construct(self):
        paper_id = self.paper_id
        # 存储相关的paper的id
        relevant_paper_ids = []

        paper_title = self.my_set.find_one({"paper_id": paper_id})["title"]
        try:
            ref_list = self.my_set.find_one({"paper_id": paper_id})["ref_id"]
        except:
            ref_list = []
            logging.error("error happen in read data from mongodb")

        print len(ref_list)
        # print "引用文章id: ", ref_list
        ref_title_list = []
        for ref_id in ref_list:
            ref_title_list.append(self.my_set.find_one({"paper_id": ref_id})["title"])
            relevant_paper_ids.append(ref_id)
        # print "ref_title_list: ", ref_title_list

        # 处理根节点与第一层引用节点的关系
        for ref_title in ref_title_list:
            self.Graph.add_edge(paper_title, ref_title)
            print "引用文章id: ", ref_title

        try:
            time_start = time.time()
            result = self.my_set.find(filter={"ref_id": paper_id})
            time_end = time.time()
            print "query time: ", time_end - time_start
        except:
            result = []
            logging.error("error happen in read data from mysql")
        # print len(result)
        # print "被引用文章id： ", result

        for paper_info in result:
            title = paper_info["title"]
            id = paper_info["paper_id"]
            self.Graph.add_edge(title, paper_title)
            print "被引用文章id： ", title
            relevant_paper_ids.append(id)

        # 存储第二层引用节点的数组
        second_layer_ref_ids = []

        # 处理第一层引用节点与第二层引用节点的关系
        print "第一层节点与第二层节点（第一层之间）关系建立"

        for relevant_paper_id in relevant_paper_ids:
            time_start = time.time()
            # 查询引用文章的引用
            rel_ref_ids = self.my_set.find_one({"paper_id": relevant_paper_id})["ref_id"]
            time_end = time.time()
            # print "query time", time_end-time_start
            for rel_ref_id in rel_ref_ids:

                if rel_ref_id not in second_layer_ref_ids:
                    second_layer_ref_ids.append(rel_ref_id)

                # if rel_ref_id in relevant_paper_ids:

                relevant_paper_title = self.query_paper_title(relevant_paper_id)
                rel_ref_title = self.query_paper_title(rel_ref_id)
                print relevant_paper_title, "引用", rel_ref_title
                self.Graph.add_edge(relevant_paper_title, rel_ref_title)

        # 处理第二层节点之间的关系
        print "第二层节点之间关系建立"
        for ref2_id in second_layer_ref_ids:
            # 查询第二层节点的引用
            ref_ref2_ids = self.my_set.find_one({"paper_id": ref2_id})["ref_id"]
            for ref_ref2_id in ref_ref2_ids:
                # 第二层节点引用第二层节点的情况
                if ref_ref2_id in second_layer_ref_ids:
                    ref_ref2_title = self.query_paper_title(ref_ref2_id)
                    ref2_title = self.query_paper_title(ref2_id)
                    print ref2_title, "引用", ref_ref2_title
                    self.Graph.add_edge(ref2_title, ref_ref2_title)

                # 第二层节点引用第一层节点的情况
                if ref_ref2_id in relevant_paper_id:
                    print "反引用："
                    ref_ref2_title = self.query_paper_title(ref_ref2_id)
                    ref2_title = self.query_paper_title(ref2_id)
                    print ref2_title, "引用", ref_ref2_title
                    self.Graph.add_edge(ref2_title, ref_ref2_title)

                    # for relevant_paper_id in relevant_paper_ids:
        # # 查询引用paper引用文章的papers
        #     ref_rels = self.my_set.find({"ref_id": relevant_paper_id})
        #
        #     for ref_rel in ref_rels:
        #         ref_rel_id = ref_rel["paper_id"]
        #         if ref_rel_id in relevant_paper_ids:
        #             relevant_paper_title = self.query_paper_title(relevant_paper_id)
        #             ref_rel_title = self.query_paper_title(ref_rel_id)
        #             print ref_rel_title, "引用", relevant_paper_title
        #             self.Graph.add_edge(ref_rel_title, relevant_paper_title)

        print "第二层节点数：", len(second_layer_ref_ids)
        # print "edges: ", self.Graph.edges()
        # print "node: ", self.Graph.nodes()

        # colors = []
        # for node in self.Graph.nodes():
        #     print node
        #     if str(node) == paper_title:
        #         colors.append('r')
        #     else:
        #         colors.append('b')
        #
        # # nx.draw(self.Graph, with_labels=True)
        # nx.draw(self.Graph, node_size=100, width=0.3,
        #         # pos=nx.spring_layout(self.Graph),
        #         node_color=colors)
        # plt.savefig(paper_id + "_modify")
        # plt.show()

    # def construct_from_source(self, paper_id):

    def query_paper_title(self, paper_id):
        """
        根据id查询title
        :param paper_id:
        :return:
        """
        paper_title = self.my_set.find_one({"paper_id": paper_id})["title"]
        return paper_title

    def edges(self):
        return self.Graph.edges()

class ConstructCoauthorsTree():

    def __init__(self, author_name, year):
        self.Graph = nx.Graph()
        self.client = pymongo.MongoClient('localhost', 27017)
        self.mongdb = self.client.Paper
        self.my_set = self.mongdb.Co_authors_added_year
        self.author_name = author_name
        self.year = year

    def construct(self):
        author_name = self.author_name
        year = self.year
        author_list=[]
        try:
            author_list = self.my_set.find({"co_authors": author_name, "year": year})
        except:
            logging.error("no such name")
        self.Graph.add_node(author_name, name=author_name)
        for author in author_list:
            co_author_list = author["co_authors"]
            for co_author_name in co_author_list:
                if co_author_name is not author_name:
                    if self.Graph.has_edge(author_name, co_author_name):
                        self.Graph[author_name][co_author_name]['weight'] += 1
                    else:
                        self.Graph.add_node(co_author_name, name=co_author_name)
                        self.Graph.add_edge(author_name, co_author_name, weight=1)

        # pos = nx.spring_layout(self.Graph)
        # labels = [self.Graph[u][v]['weight'] for u,v in self.Graph.edges()]
        # print 'weight: ', labels
        # nx.draw(self.Graph, pos, with_labels=True, width=labels)
        #
        # plt.savefig(author_name+str(year))
        # plt.show()

        # print author_list

    def edges(self):
        return self.Graph.edges()

    def all_nodes(self):
        nodes = self.Graph.nodes()
        return nodes
                # print author_list


    def all_edges(self):
        edges = self.Graph.edges()
        edges_list = []
        for u,v in edges:
            if u==v:
                continue
            else:
                w = self.Graph[u][v]["weight"]
                edge = (u,v,w)
                edges_list.append(edge)
        return edges_list

if __name__ == "__main__":
    # CTM = ConstructCitationTree()
    # CTM.construct("00338203-9eb3-40c5-9f31-cbac73a519ec")
    # years = [2008, 2009, 2010, 2011, 2012, 2013]
    # for year in years:
    CCT = ConstructCoauthorsTree("Martin Ester", 2010)
    CCT.construct()
    # print CCT.all_edges()
    for u,v,w in CCT.all_edges():
        print u,v,w