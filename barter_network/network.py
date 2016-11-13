import networkx as nx
# from networkx.readwrite import json_graph
import matplotlib
# Force matplotlib to not use any Xwindows backend.
matplotlib.use('Agg')

import matplotlib.pyplot as plt
# createdb -E UTF8 -T template0 --locale=en_US.utf8 barternet



from model import connect_to_db, db, User, Skill, UserSkill
# from server import app
from barter_network import app
connect_to_db(app)

FILE_PATH = 'barter_network/static'

nodes = db.session.query(UserSkill.user_id,User.user_fname).join(User).all() 
skill_to = UserSkill.query.filter(UserSkill.skill_direction =='to').all()
skill_from = db.session.query(UserSkill,Skill.skill_name).join(Skill).filter(UserSkill.skill_direction=='from').all()


Z = nx.DiGraph()
Z.clear

def add_nodes(data):
    for a in data:
        Z.add_node(a[0],name=a[1])
    # print Z.nodes(data=True)

add_nodes(nodes)

def add_edges(skill_to, skill_from):
    for x, name_s in skill_from:
        Z.add_edges_from([(x.user_id, y.user_id, {'name': name_s})for y in skill_to if x.skill_id == y.skill_id])
    # print Z.edges(data=True)
 

add_edges(skill_to, skill_from)

def create_graph(graph=Z):
    plt.figure(1)
    pos = nx.spring_layout(Z)
    nx.draw(Z, pos, node_color="r",edge_color='blue', #with_labels=True,
        alpha=0.5, node_size=700, width=1, font_size=15, scale=30)
    node_labels = nx.get_node_attributes(Z, 'name')
    nx.draw_networkx_labels(Z, pos, labels=node_labels)
    edge_labels = nx.get_edge_attributes(Z, 'name')
    nx.draw_networkx_edge_labels(Z, pos, labels=edge_labels)
    plt.savefig(FILE_PATH+'/graph1.png')

create_graph(Z)


# def save(G, fname):
#     json.dump(dict(nodes=[[n, G.node[n]] for n in G.nodes()],
#                    edges=[[u, v, G.edge[u][v]] for u,v in G.edges()]),
#               open(fname, 'w'), indent=2)
# save(Z, 'static/graph1.json')


# def find_closed_loop(Z):
#     print [loop for loop in nx.simple_cycles(Z)]
        
# print list(nx.simple_cycles(Z))
one = [line for line in list(nx.simple_cycles(Z)) if line[0]==5]
B = nx.DiGraph()
B.clear

# print len(one[0])
ls=[]
for i in range(len(one[0])-1):
    ls.append((one[0][i:i+2]))
ls.append((one[0][-1],one[0][0]))

# ls=[(one[0][0:2]),(one[0][1:3]),(one[0][2:4]),(one[0][3:5]),(one[0][-1],one[0][0])]


# for i in one[0]:
#     print nx.edges(Z,[i])
#     print Z.out_edges(i)

plt.figure(2)
B.add_nodes_from(one[0])
B.add_edges_from(ls)
nx.draw_networkx(B, with_labels=True)
plt.savefig('barter_network/static/loop1.png')



##################################
from itertools import chain, count
import json
# import networkx as nx
from networkx.utils import make_str
__author__ = """Aric Hagberg <hagberg@lanl.gov>"""
__all__ = ['node_link_data', 'node_link_graph']


_attrs = dict(id='id', source='source', target='target', key='key')


def node_link_data(G, attrs=_attrs):
    """Return data in node-link format that is suitable for JSON serialization
    and use in Javascript documents.

    Parameters
    ----------
    G : NetworkX graph

    attrs : dict
        A dictionary that contains four keys 'id', 'source', 'target' and
        'key'. The corresponding values provide the attribute names for storing
        NetworkX-internal graph data. The values should be unique. Default
        value:
        :samp:`dict(id='id', source='source', target='target', key='key')`.

        If some user-defined graph data use these attribute names as data keys,
        they may be silently dropped.

    Returns
    -------
    data : dict
       A dictionary with node-link formatted data.

    Raises
    ------
    NetworkXError
        If values in attrs are not unique.

    Examples
    --------
    >>> from networkx.readwrite import json_graph
    >>> G = nx.Graph([(1,2)])
    >>> data = json_graph.node_link_data(G)

    To serialize with json

    >>> import json
    >>> s = json.dumps(data)

    Notes
    -----
    Graph, node, and link attributes are stored in this format. Note that
    attribute keys will be converted to strings in order to comply with
    JSON.

    The default value of attrs will be changed in a future release of NetworkX.

    See Also
    --------
    node_link_graph, adjacency_data, tree_data
    """
    multigraph = G.is_multigraph()
    id_ = attrs['id']
    source = attrs['source']
    target = attrs['target']
    # Allow 'key' to be omitted from attrs if the graph is not a multigraph.
    key = None if not multigraph else attrs['key']
    if len(set([source, target, key])) < 3:
        raise nx.NetworkXError('Attribute names are not unique.')
    mapping = dict(zip(G, count()))
    data = {}
    data['directed'] = G.is_directed()
    data['multigraph'] = multigraph
    data['graph'] = G.graph
    data['nodes'] = [dict(chain(G.node[n].items(), [(id_, n)])) for n in G]
    if multigraph:
        data['links'] = [
            dict(chain(d.items(),
                       [(source, mapping[u]), (target, mapping[v]), (key, k)]))
            for u, v, k, d in G.edges_iter(keys=True, data=True)]
    else:
        data['links'] = [
            dict(chain(d.items(),
                       [(source, u), (target, v)]))
            for u, v, d in G.edges_iter(data=True)]

    return data

# data = json_graph.node_link_data(Z)
def json_my_net_data(Z):
    data = node_link_data(Z)
    with open(FILE_PATH+'/graph1.json', 'w') as f:
        json.dump(data,f,indent=4)

json_my_net_data(Z)

def json_my_smallnet_data(B):
    data = node_link_data(B)
    with open('barter_network/static/smallgraph.json', 'w') as f:
        json.dump(data,f,indent=4)
        
json_my_smallnet_data(B)





if __name__ == '__main__':

    FILE_PATH = '/static'




