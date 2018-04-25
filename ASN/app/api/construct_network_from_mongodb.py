# -*- coding:utf-8 -*-
import pymongo
import MySQLdb
import networkx as nw
import matplotlib.pyplot as plt
import logging
import time
import sys

reload(sys)
sys.setdefaultencoding("utf-8")


class ConstructCitationTree():

    def __init__(self, paper_id):
        self.Graph = nw.DiGraph()
        self.client = pymongo.MongoClient('localhost', 27017)
        self.mongdb = self.client.Paper
        self.my_set = self.mongdb.Citation_added_title_year
        # self.my_set = self.mongdb.Citation
        self.paper_id = paper_id

        self.node_limit = 30
        self.total_node_list = []

    def construct(self):
        paper_id = self.paper_id
        self.total_node_list.append((paper_id))


        relevant_paper_ids = [] # 存储相关的paper的id (第一层节点 即引用root和被root引用的论文)
        root = self.my_set.find_one({"paper_id": paper_id})
        paper_title = root["title"]
        year = root["title"]
        self.Graph.add_node(paper_id, paper_title=paper_title, id=paper_id, year=year)

        # 查询根节点的引用论文id (node → root)
        try:
            ref_list = self.my_set.find_one({"paper_id": paper_id})["ref_id"]
        except:
            ref_list = []
            logging.error("error happen in read data from mongodb")


        print len(ref_list)
        # print "引用文章id: ", ref_list
        ref_title_list = []
        for ref_id in ref_list:
            ref_node = self.my_set.find_one({"paper_id": ref_id})
            ref_title_list.append((ref_node['paper_id'], ref_node['title'], ref_node['year']))
            relevant_paper_ids.append(ref_id)
        # print "ref_title_list: ", ref_title_list

        # 处理root与第一层引用root的节点的关系
        for ref_id, ref_title, ref_year in ref_title_list:

            self.total_node_list.append(ref_id)

            self.Graph.add_node(ref_id, paper_title=ref_title, id=ref_id, year=ref_year)
            self.Graph.add_edge(paper_id, ref_id)
            print "引用文章id: ", ref_title

        # 查询引用根节点的论文 (node ← root)
        try:
            time_start = time.time()
            result = self.my_set.find(filter={"ref_id": paper_id})
            time_end = time.time()
            print "query time: ", time_end - time_start
        except:
            result = []
            print "error"
            logging.error("error happen in read data from mongo")
        # print len(result)
        # print "被引用文章id： ", result

        for paper_info in result:
            title = paper_info['title']
            id = paper_info['paper_id']
            year = paper_info['year']

            # 如果总节点数超过限制，则终止循环
            if len(self.total_node_list) > self.node_limit:
                # print "break in 处理第一层引用节点与根节点的关系"
                break
            if id not in self.total_node_list:
                self.total_node_list.append(id)

            self.Graph.add_node(id, paper_title=title, id=id, year=year)
            self.Graph.add_edge(id, paper_id)
            print "被引用文章id： ", title
            relevant_paper_ids.append(id)




        second_layer_ref_ids = [] # 存储第二层节点的数组

        # 处理第一层引用节点与第二层引用节点的关系
        # print "第一层节点与第二层节点（第一层之间）关系建立"

        for relevant_paper_id in relevant_paper_ids:

            # # 如果总节点数超过限制，则终止循环 ###############################
            if len(self.total_node_list) > self.node_limit:
                # print "break in 处理第一层引用节点与第二层引用节点的关系：1"
                break
            if relevant_paper_id not in self.total_node_list:
                self.total_node_list.append(relevant_paper_id)




            # 查询第一层节点引用的论文(node1 ← node2)
            time_start = time.time()
            rel_node = self.my_set.find_one({"paper_id": relevant_paper_id})
            time_end = time.time()
            # print "query time", time_end-time_start

            rel_ref_ids = rel_node['ref_id']
            relevant_paper_title = rel_node['title']

            # self.Graph.add_node(
            #     rel_node['paper_id'],
            #     paper_title=rel_node['title'],
            #     id=rel_node['paper_id'],
            #     year=rel_node['year']
            # )

            for rel_ref_id in rel_ref_ids:

                # # 如果总节点数超过限制，则终止循环 ###############################
                if len(self.total_node_list) > self.node_limit:
                    # print "break in 处理第一层引用节点与第二层引用节点的关系：2"
                    break
                if rel_ref_id not in self.total_node_list:
                    self.total_node_list.append(rel_ref_id)


                if rel_ref_id not in second_layer_ref_ids:
                    second_layer_ref_ids.append(rel_ref_id)


                rel_ref_id, rel_ref_title, rel_ref_year\
                    = self.query_paper_id_title_year(rel_ref_id)
                self.Graph.add_node(
                    rel_ref_id,
                    paper_title=rel_ref_title,
                    id=rel_ref_id,
                    year=rel_ref_year
                )
                self.Graph.add_edge(relevant_paper_id, rel_ref_id)
                print relevant_paper_title, "引用", rel_ref_title


            # 引用第一层节点的论文(node1 → node2)
            try:
                time_start = time.time()
                ref2_rel1_nodes = self.my_set.find(filter={"ref_id": relevant_paper_id})
                time_end = time.time()
                print "query time: ", time_end - time_start
            except:
                ref2_rel1_nodes = []
                print "error"
                logging.error("error happen in read data from mongo")

            for ref2_rel1_node in ref2_rel1_nodes:
                title = ref2_rel1_node['title']
                id = ref2_rel1_node['paper_id']
                year = ref2_rel1_node['year']
                # print "引用第一层节点的文章：", title

                # # 如果总节点数超过限制，则终止循环 ###############################
                if len(self.total_node_list) > self.node_limit:
                    # print "break in 处理第一层引用节点与根节点的关系"
                    break
                if id not in self.total_node_list:
                    self.total_node_list.append(id)

                self.Graph.add_node(id, paper_title=title, id=id, year=year)
                self.Graph.add_edge(id, paper_id)
                print "被引用文章id： ", title
                if id not in second_layer_ref_ids:
                    second_layer_ref_ids.append(id)


        # 处理第二层节点之间的关系 （此过程没有添加节点）
        print "第二层节点之间关系建立"
        for ref2_id in second_layer_ref_ids:

            # # 如果总节点数超过限制，则终止循环 ###############################
            # if len(self.total_node_list) > self.node_limit:
            #     print "break in 处理第二层节点之间的关系: 1"
            #     break
            # if ref2_id not in self.total_node_list:
            #     self.total_node_list.append(ref2_id)

            ref2_id, ref2_title, ref2_year = self.query_paper_id_title_year(ref2_id)
            self.Graph.add_node(ref2_id, paper_title=ref2_title, id=ref2_id, year=ref2_year)

            # 查询第二层节点的引用
            ref_ref2_ids = self.my_set.find_one({"paper_id": ref2_id})["ref_id"]
            for ref_ref2_id in ref_ref2_ids:

                # # 如果总节点数超过限制，则终止循环 ###############################
                # if len(self.total_node_list) > self.node_limit:
                #     print "break in 处理第二层节点之间的关系: 2"
                #     break
                # if ref_ref2_id not in self.total_node_list:
                #     self.total_node_list.append(ref_ref2_id)

                # 第二层节点引用第二层节点的情况
                if ref_ref2_id in second_layer_ref_ids:
                    ref_ref2_id, ref_ref2_title, ref_ref2_year = self.query_paper_id_title_year(ref_ref2_id)
                    # print ref2_title, "引用", ref_ref2_title
                    self.Graph.add_node(ref_ref2_id, paper_title=ref_ref2_title, id=ref_ref2_id, year=ref_ref2_year)
                    self.Graph.add_edge(ref2_id, ref_ref2_id)

                # 第二层节点(第一层节点)引用第一层节点的情况
                if ref_ref2_id in relevant_paper_ids:
                    # print "反引用："
                    ref_ref2_id, ref_ref2_title, ref_ref2_year = self.query_paper_id_title_year(ref_ref2_id)
                    self.Graph.add_node(ref_ref2_id, paper_title=ref_ref2_title, id=ref_ref2_id, year=ref_ref2_year)
                    # ref2_id, ref2_title, ref2_year = self.query_paper_id_title_year(ref2_id)
                    # print ref2_title, "引用", ref_ref2_title
                    self.Graph.add_edge(ref2_id, ref_ref2_id)

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
        #     # print node
        #     if str(node) == paper_id:
        #         colors.append('r')
        #     else:
        #         colors.append('b')
        #
        # # nx.draw(self.Graph, with_labels=True)
        # nw.draw(self.Graph, node_size=100, width=0.3,
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

    def query_paper_id_title_year(self, paper_id):
        """
        返回论文的(id, title, year)
        :param paper_id:
        :return:
        """
        paper =  self.my_set.find_one({"paper_id": paper_id})
        title = paper['title']
        year = paper['year']
        return (paper_id, title, year)


    def edges(self):
        return self.Graph.edges()

    def nodes(self):
        return self.Graph.nodes()

    def all_nodes(self):
        node_list = []
        nodes = self.Graph.nodes()
        for i, node in enumerate(nodes):
            pi = self.Graph.node[node]['id']
            # print "pi", pi
            t = self.Graph.node[node]['paper_title']
            # print "t", t
            y = self.Graph.node[node]['year']
            # print "y", y
            node_list.append((pi,t,y))
        return node_list

    def num_of_nodes(self):
        return self.Graph.number_of_nodes()

class ConstructCoauthorsTree():

    def __init__(self, author_name, year):
        self.Graph = nw.DiGraph()
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

    def nodes_num(self):
        """
        返回节点数量
        :return:
        """
        return self.Graph.number_of_nodes()

if __name__ == "__main__":
    CTM = ConstructCitationTree("00338203-9eb3-40c5-9f31-cbac73a519ec")
    CTM.construct()
    # print CTM.all_nodes()

    print "num: ", CTM.num_of_nodes()
    # years = [2008, 2009, 2010, 2011, 2012, 2013]
    # for year in years:

    # CCT = ConstructCoauthorsTree("Martin Ester", 2010)
    # CCT.construct()
    # print CCT.all_edges()
    # for u,v,w in CCT.all_edges():
    #     print u,v,w