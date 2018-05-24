# -*- coding:utf-8 -*-
import pymongo
import numpy as np
import networkx as nx
from collections import defaultdict
import matplotlib.pyplot as plt
import logging
import time
import MySQLdb
import sys

reload(sys)
sys.setdefaultencoding("utf-8")


class NewConstructCitationTree():
    def __init__(self, paper_id):
        self.Graph = nx.DiGraph()
        self.client = pymongo.MongoClient('localhost', 27017)
        self.mongdb = self.client.Paper
        self.my_set = self.mongdb.citation_total
        self.paper_id = paper_id

        self.node_limit_num = 100 - 1
        # self.node_limit_num = 'inf'
        self.total_node_list = []
        self.init_cata = 0

        self.iter_time = 200
        self.smallest_community_node_num = 2

    def construct(self):

        paper_id = self.paper_id  # root 节点
        self.total_node_list.append((paper_id))

        # 在图中加入 root 节点
        root = self.my_set.find_one({"paper_id": paper_id})
        paper_title = root["title"]
        year = root["title"]
        self.Graph.add_node(paper_id, paper_title=paper_title, id=paper_id, year=year, cata=self.init_cata)

        first_layer_paper_ids = list()  # 存储相关的paper的id (第一层节点 即引用root和被root引用的论文)

        # 添加root引用的节点和建立边，并更新layer_list
        first_layer_paper_ids = self.add_nodes_and_edges_to_root(paper_id, first_layer_paper_ids)
        print "len of layer 1: ", len(first_layer_paper_ids)
        # 添加引用root的节点和建立边，并更新layer_list
        first_layer_paper_ids = self.add_nodes_and_edges_from_root(paper_id, first_layer_paper_ids)
        print "len of layer 1: ", len(first_layer_paper_ids)

        second_layer_paper_ids = list()  # 存储第二层节点 即引用第一层节点(node1)或 第一层节点(node1)引用的节点

        for id1 in first_layer_paper_ids:
            # 添加node1引用的节点和建立边，并更新next_layer_list (如果在layer1中存在node1引用的节点，在此建立边)
            second_layer_paper_ids = self.add_nodes_and_edges_to_root(id1, second_layer_paper_ids)

            # 添加引用node1的节点和建立边，并更新next_layer_list (如果在layer1中存在node1引用的节点，在此建立边)
            second_layer_paper_ids = self.add_nodes_and_edges_from_root(id1, second_layer_paper_ids)

        # layer2 之内建立节点之间的边
        pure_third_layer_paper_ids = self.build_relationship_in_layer_and_get_next_layer_id_list(second_layer_paper_ids)

        # colors = []
        # for node in self.Graph.nodes():
        #     # print node
        #     if str(node) == paper_id:
        #         colors.append('r')
        #     else:
        #         colors.append('b')
        #
        # nx.draw(self.Graph, node_size=100, width=0.3, node_color=colors)
        # plt.savefig(paper_id + "_modify")
        # plt.show()

    def build_relationship_in_layer_and_get_next_layer_id_list(self, layer_list):
        """
        建立层内节点间的边， 得到下一层的节点列表
        :param layer_list: 建立边的layer
        :param next_layer_list: 下一层layer
        :return:
        """
        next_layer_list = []  # 下一层layer不包含本层layer节点

        for id in layer_list:
            title, year = self.query_paper_id_title_year(id)

            ## 查询 id 的引用节点 ##
            id_ref_list = self.my_set.find_one({'paper_id': id})['ref_id']

            for id_ref in id_ref_list:
                if id_ref in layer_list:
                    # 查询
                    id_ref_title, id_ref_year = self.query_paper_id_title_year(id_ref)
                    # 添加节点和相应的边
                    self.Graph.add_node(id_ref, paper_title=id_ref_title, id=id_ref, year=id_ref_year,
                                        cata=self.init_cata)
                    self.Graph.add_edge(id, id_ref)
                    # print title, '引用', id_ref_title
                else:
                    next_layer_list.append(id_ref)

            ## 查询引用 id 的节点 ##
            try:
                ref_node_list = self.my_set.find(filter={"ref_id": id})
            except:
                ref_node_list = []
                print "error"
                logging.error("error happen in read data from mongo")

            for node in ref_node_list:
                ref_id_title = node['title']
                ref_id = node['paper_id']
                ref_id_year = node['year']
                if ref_id in layer_list:
                    # 添加节点和相应的边
                    self.Graph.add_node(ref_id, paper_title=ref_id_title, id=ref_id, year=ref_id_year,
                                        cata=self.init_cata)
                    self.Graph.add_edge(ref_id, id)
                    # print ref_id_title, '引用', title

                else:
                    next_layer_list.append(ref_id)
        return next_layer_list

    def add_nodes_and_edges_to_root(self, root_id, layer_list):
        """
        添加一个 root 节点和其所有的引用节点的边
        :param root_id:
        :param id_list: root 引用的节点
        :return:
        """

        root_title, root_year = self.query_paper_id_title_year(root_id)
        # 查询
        try:
            id_list = self.my_set.find_one({'paper_id': root_id})['ref_id']
        except:
            id_list = []
            logging.error("error happen in read data from mongo")

        for id in id_list:

            # 限制节点数
            if len(self.total_node_list) > self.node_limit_num:
                break
            else:
                if id not in self.total_node_list:
                    self.total_node_list.append(id)
                if id not in layer_list:
                    layer_list.append(id)

            title, year = self.query_paper_id_title_year(id)
            self.Graph.add_node(id, paper_title=title, id=id, year=year, cata=self.init_cata)
            self.Graph.add_edge(root_id, id)
            # print root_title, '引用', title
        return layer_list

    def add_nodes_and_edges_from_root(self, root_id, layer_list):
        """
        添加所有引用root节点的节点的边
        :param root_id:
        :param id_list: 引用root的所有节点
        :return:
        """
        root_title, root_year = self.query_paper_id_title_year(root_id)
        # 查询引用根节点的论文 (node 引用 root)
        try:
            node_list = self.my_set.find(filter={"ref_id": root_id})
        except:
            node_list = []
            print "error"
            logging.error("error happen in read data from mongo")

        for node in node_list:
            title = node['title']
            id = node['paper_id']
            year = node['year']

            # 限制节点数
            if len(self.total_node_list) > self.node_limit_num:
                break
            else:
                if id not in self.total_node_list:
                    self.total_node_list.append(id)
                if id not in layer_list:
                    layer_list.append(id)

            # 添加节点和相应的边
            self.Graph.add_node(id, paper_title=title, id=id, year=year, cata=self.init_cata)
            self.Graph.add_edge(id, root_id)
            # print title, '引用', root_title
        return layer_list

    def community_detection(self):
        H = self.Graph.to_undirected()
        klist = list(nx.k_clique_communities(H, 3))
        pos = nx.spring_layout(H)
        plt.clf()

        nx.draw(H, pos=pos, with_labels=False)

        for index, cata in enumerate(klist):
            for node in cata:
                # print "node1:", node
                # print "node2:", H.node[node]
                self.Graph.node[node]['cata'] = index + 1
        # nx.draw(self.Graph, pos=pos, nodelist=cata, node_color=colors[index])
        # plt.show()
        print "klist:", len(klist)
        return len(klist) + 1

    def community_detection_slpa(self):
        # 迭代次数
        T = self.iter_time
        # 将图中数据录入到数据字典中以便使用
        # G = self.Graph.to_undirected()
        G = self.Graph
        # 建立成员标签记录
        memory = {i: {i: 1} for i in G.nodes()}
        # print "memory", memory
        # 开始遍历T次所有节点
        for t in range(T):
            listenerslist = list(G.nodes())
            # print "listenerslist", listenerslist
            # 随机排列遍历顺序
            np.random.shuffle(listenerslist)
            # 开始遍历节点
            for listener in listenerslist:
                # 每个节点的key就是与他相连的节点标签名
                # speakerlist = G[listener].keys()
                speakerlist = G.neighbors(listener)
                if len(speakerlist) == 0:
                    continue
                labels = defaultdict(int)
                # print "labels", labels
                # 遍历所有与其相关联的节点
                for j, speaker in enumerate(speakerlist):
                    total = float(sum(memory[speaker].values()))
                    # 查看speaker中memory中出现概率最大的标签并记录，key是标签名，value是Listener与speaker之间的权
                    # np.random.multinomial(1，seq),根据数列seq概率随机选择seq中的1个
                    labels[memory[speaker].keys()[np.random.multinomial(1, [freq / total for freq in memory[speaker].values()]).argmax()]] += 1
                    # print "labels", labels

                # 查看labels中值最大的标签，若不存在于memory的listener中，让其成为当前listener的一个记录，若存在，增加value的值
                maxlabel = max(labels, key=labels.get)
                # print "maxlabel", maxlabel
                if maxlabel in memory[listener]:
                    memory[listener][maxlabel] += 1
                else:
                    memory[listener][maxlabel] = 1

        # 提取出每个节点memory中记录标签出现最多的一个
        for primary in memory:
            # print "freq", memory[primary].values()
            # print "total", total
            # print "multinomial: ", [freq / total for freq in memory[primary].values()]
            # print "after: ", np.random.multinomial(1, [freq / total for freq in memory[primary].values()])
            # print "after_m: ", np.argmax(memory[primary].values())
            # p = memory[primary].keys()[
            #     np.random.multinomial(1, [freq / total for freq in memory[primary].values()]).argmax()]
            # memory[primary] = {p: memory[primary][p]}
            p = memory[primary].keys()[np.argmax(memory[primary].values())]
            memory[primary] = {p: memory[primary][p]}


        communities = {}
        # 扫描memory中的记录标签，相同标签的节点加入同一个社区中
        for primary, change in memory.iteritems():
            for label in change.keys():
                if label in communities:
                    communities[label].add(primary)
                else:
                    communities[label] = set([primary])
        freecommunities = set()
        keys = communities.keys()

        # pos = nx.spring_layout(G)

        #  过滤节点小于一定数目的社区
        new_communities = []
        for index, com in enumerate(communities.keys()):
            if len(communities[com]) > self.smallest_community_node_num:
                for node in communities[com]:
                    self.Graph.node[node]['cata'] = len(new_communities) + 1
                new_communities.append(communities[com])
            else:
                for node in communities[com]:
                    self.Graph.node[node]['cata'] = 0

        return len(new_communities) + 1

    def query_paper_id_title_year(self, paper_id):
        """
        返回论文的(id, title, year)
        :param paper_id:
        :return:
        """
        paper = self.my_set.find_one({"paper_id": paper_id})
        title = paper['title']
        year = paper['year']
        return (title, year)

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
            c = self.Graph.node[node]['cata']

            d = self.Graph.in_degree(pi) + 5
            # if d > 50:
            #     d -= 30

            node_list.append((pi, t, y, c, d))
        return node_list

    def num_of_nodes(self):
        return self.Graph.number_of_nodes()


class ConstructCoauthorsTree():
    def __init__(self, author_name, year):
        self.Graph = nx.DiGraph()
        self.client = pymongo.MongoClient('localhost', 27017)
        self.mongdb = self.client.Paper
        self.my_set = self.mongdb.citation_total
        self.author_name = author_name
        self.year = year
        self.db = MySQLdb.connect(host="47.106.157.16", user="root", passwd="123456", db="citation")

    def construct(self):
        author_name = self.author_name
        year = self.year
        author_list = []
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
                        self.Graph.add_node(
                            co_author_name, name=co_author_name,
                            department="", phone="", avatar="",
                            address="", gender="", position=""
                        )

                        self.Graph.add_edge(author_name, co_author_name, weight=1)
        self.query_expert_detail()

    def query_expert_detail(self):
        """
        查询所有
        :return:
        """
        sql = "select position, department, address, phone, avatar, gender  from expert_user_detail where name = '%s'"

        for node in self.Graph.nodes():
            print "node", node, type(node)
            exe_sql = sql % node
            cursor = self.db.cursor()
            cursor.execute(exe_sql)
            result = cursor.fetchall()

            if len(result) == 1:
                position = result[0][0]
                department = result[0][1]
                address = result[0][2]
                phone = result[0][3]
                avatar = result[0][4]
                gender = result[0][5]

                self.Graph.node[node]['position'] = position
                self.Graph.node[node]['department'] = department
                self.Graph.node[node]['address'] = address
                self.Graph.node[node]['phone'] = phone
                self.Graph.node[node]['avatar'] = avatar
                self.Graph.node[node]['gender'] = gender

    def edges(self):
        return self.Graph.edges()

    def all_nodes(self):
        """
        返回所有节点信息
        :return:
        """
        nodes_list = list()
        nodes = self.Graph.nodes()
        for node in nodes:
            name = self.Graph.node[node]['name']
            position = self.Graph.node[node]['position']
            department = self.Graph.node[node]['department']
            address = self.Graph.node[node]['address']
            phone = self.Graph.node[node]['phone']
            avatar = self.Graph.node[node]['avatar']
            gender = self.Graph.node[node]['gender']
            if avatar is "":
                avatar = "../static/common/img/init.png"

            if gender is "":
                gender = "unknown"

            if position == "[]":
                position = ""

            if position == []:
                print "fuck list"
                position = ""

            new_node = (name, position, department, address, phone, avatar, gender)
            nodes_list.append((new_node))
        return nodes_list
        # print author_list

    def all_edges(self):
        edges = self.Graph.edges()
        edges_list = list()
        for u, v in edges:
            if u == v:
                continue
            else:
                w = self.Graph[u][v]["weight"]
                edge = (u, v, w)
                edges_list.append(edge)
        return edges_list

    def nodes_num(self):
        """
        返回节点数量
        :return:
        """
        return self.Graph.number_of_nodes()


if __name__ == "__main__":
    CTM = NewConstructCitationTree("62e74114-e52b-4441-b39c-6cab360ad9ed")
    CTM.construct()
    CTM.community_detection()
    # CTM.community_detection_slpa(5, 3)
    print CTM.all_nodes()

    print "num: ", CTM.num_of_nodes()
    # years = [2008, 2009, 2010, 2011, 2012, 2013]
    # for year in years:

    # CCT = ConstructCoauthorsTree("Martin Ester", 2010)
    # CCT.construct()
    # print CCT.all_edges()
    # for u,v,w in CCT.all_edges():
    #     print u,v,w
