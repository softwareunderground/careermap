import difflib
import shelve
from datetime import datetime
import networkx as nx
import base64
from io import BytesIO
import matplotlib.pyplot as plt
import numpy as np


VOCAB = ["undergrad", "postgrad", "faculty", "academic",
         "service", "software", "technology",
         "consulting", "sales",
         "natoc", "intoc", "indoc", "junoc",
         "government", "agency", "survey", "localgov",
         "mining",
         "unemployed", "retired",
         "startup", "self-employed",
         "other", 'break'
        ]

def get_info(record):
    """
    Take a single response and turn it into a list of careers.

    Completely ignore the numbers for now.
    """
    items = [tuple(i.strip().split()) for i in record.split(',')]
    items = filter(None, items)
    path, years = [], {}
    for pair in items:
        # Get employment.
        m = difflib.get_close_matches(pair[0], VOCAB, n=1, cutoff=0.5)
        if m:
            job = m[0]
        else:
            job = 'other'
        path.append(job)

        # Get years.
        try:
            y = float(pair[1])
        except ValueError:  # Garbled number
            y = 1
        except IndexError:  # None provided
            y = 1
        years[job] = y

    return path, years


def store(record):
    _ = store_entry(record)
    path, years = get_info(record)
    with shelve.open('edges') as db:
        for pair in zip(path[:-1], path[1:]):
            count = db.get(','.join(pair), 0)
            db[','.join(pair)] = count + 1
    with shelve.open('nodes') as db:
        for k, v in years.items():
            vi = db.get(k, 0)
            db[k] = vi + v
    return 'Thank you!'


def store_entry(data):
    with open('log.txt', 'ta') as f:
        d = datetime.utcnow().isoformat() + '\t'
        f.write(d + data + '\n')
    return 'Done'


def get_network(years):
    """
    Get the network from the Shelf.
    """
    G = nx.Graph()
    G.add_nodes_from([(k, {'count': v}) for k, v in years.items()])
    with shelve.open('edges') as db:
        for e, w in db.items():
            u, v = e.split(',')
            G.add_edge(u, v, weight=w)

    G.remove_nodes_from(list(nx.isolates(G)))
    return G


def get_years():
    with shelve.open('nodes') as db:
        d = dict(db).copy()

    return d


def plot_network(G, years, scale=10):
    """
    Make a networkx plot and convert to base64-encoded string.
    """

    print(nx.__version__)

    edges = G.edges()
    weights = [G[u][v]['weight'] for u,v in edges]

    print(nx.get_node_attributes(G, 'count'))
    counts = [scale * nx.get_node_attributes(G, 'count')[u] for u in G.nodes()]

    params = {
        'node_size': counts,
        'with_labels': True,
        'width': weights,
    }

    pos = nx.spring_layout(G)

    fig = plt.figure(figsize=(8, 8))
    nx.draw(G, pos, **params)

    # Save as base64 string.
    handle = BytesIO()
    plt.savefig(handle, format='png', facecolor=fig.get_facecolor())
    plt.close()
    handle.seek(0)
    figdata_png = base64.b64encode(handle.getvalue())

    return figdata_png.decode('utf8')


def plot_years(data, drop=False, log=False):

    if drop:
        _ = data.pop('undergrad', None)
        _ = data.pop('retired', None)
        _ = data.pop('unemployed', None)
        _ = data.pop('break', None)

    labels = list(data.keys())
    values = list(data.values())

    values = sorted(values, reverse=True)
    labels = sorted(labels, key=lambda li: values[labels.index(li)], reverse=True)

    y = list(range(len(values)))
    y_min, y_max = y[0]-0.75, y[-1]+0.75

    fig, ax = plt.subplots(figsize=(8, 8))
    bars = ax.barh(y, values, color='orange', align='center', edgecolor='none')
    bars[np.argmax(values)].set_color('red')
    ax.set_yticks(y)
    if log:
        ax.set_xscale('log')
    ax.set_yticklabels(labels, size=12)
    ax.set_ylim(y_max, y_min)  # Label top-down.
    ax.grid(c='black', alpha=0.15, which='both')
    ax.patch.set_facecolor("white")
    fig.patch.set_facecolor("none")
    ax.set_title("{:.2f} person-careers of experience".format(sum(values)/40))

    for i, d in enumerate(values):
        ax.text(1, i, "{}".format(int(d)), va='center', size=12)

    plt.tight_layout()

    # Put in memory.
    handle = BytesIO()
    plt.savefig(handle, format='png', facecolor=fig.get_facecolor())
    plt.close()

    # Encode.
    handle.seek(0)
    figdata_png = base64.b64encode(handle.getvalue()).decode('utf8')

    return figdata_png

