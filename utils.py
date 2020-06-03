import difflib
import shelve
from datetime import datetime
import networkx as nx
import base64
from io import BytesIO
import matplotlib.pyplot as plt


VOCAB = ["student", "undergrad", "postgrad", "postdoc", "lecturer", "professor", "reader", "academic",
         "megaservice", "service", "microservice",
         "consultant", "sales",
         "software", "technology",
         "noc", "ioc", "independent", "exploration", "e&p",
         "government", "agency", "survey", "localgov",
         "mining",
         "unemployed", "retired",
         "startup", "self-employed",
         "other"
        ]


def get_path(record):
    items = [tuple(i.strip().split()) for i in record.split(',')]
    path = []
    for pair in items:
        m, = difflib.get_close_matches(pair[0], VOCAB, n=1, cutoff=0)
        path.append(m)
    return path


def store_path(path):
    with shelve.open('edges') as db:
        for pair in [*zip(path[:-1], path[1:])]:
            count = db.get(','.join(pair), 0)
            db[','.join(pair)] = count + 1
    return 'Done'


def store_entry(data):
    with open('log.txt', 'ta') as f:
        d = datetime.utcnow().isoformat() + '\t'
        f.write(d + data + '\n')
    return 'Done'


def get_network():
    """
    Get the network from the Shelf.
    """
    G = nx.Graph()
    G.add_nodes_from(VOCAB)
    with shelve.open('edges') as db:
        for e, w in db.items():
            u, v = e.split(',')
            G.add_edge(u, v, weight=w)

    G.remove_nodes_from(list(nx.isolates(G)))
    return G


def plot(G):
    """
    Make a networkx plot and convert to base64-encoded string.
    """
    edges = G.edges()
    weights = [G[u][v]['weight'] for u,v in edges]

    params = {
        'node_size': 40,
        'with_labels': True,
        'width': weights,
    }

    pos = nx.spring_layout(G)

    # fig = plt.figure()
    nx.draw(G, pos, **params)

    # Save as base64 string.
    handle = BytesIO()
    plt.savefig(handle, format='png')#, facecolor=fig.get_facecolor())
    plt.close()
    handle.seek(0)
    figdata_png = base64.b64encode(handle.getvalue())

    return figdata_png.decode('utf8')
