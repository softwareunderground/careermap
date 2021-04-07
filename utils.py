import difflib
import shelve
from datetime import datetime
import networkx as nx
import base64
from io import BytesIO
import matplotlib.pyplot as plt
from collections import OrderedDict
from collections import defaultdict


VOCAB = ["undergrad", "postgrad", "faculty", "academic",
         "service", "software", "technology",
         "consulting", "sales",
         "natoc", "intoc", "indoc", "junoc",
         "government", "agency", "survey", "localgov",
         "mining",
         "unemployed", "retired",
         "startup", "self-employed",
         "other", 'break',
         ]


def get_info(record):
    """
    Take a single response and turn it into a list of careers.

    Completely ignore the numbers for now.
    """
    items = [tuple(i.strip().split()) for i in record.split(',')]
    items = filter(None, items)
    path, years = [], defaultdict(int)
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
        years[job] += y

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
    with shelve.open('lasts') as db:
        last = path[-1]
        db[last] = db.get(last, 0) + 1
    with shelve.open('lens') as db:
        length = str(int(sum(years.values())))
        db[length] = db.get(length, 0) + 1
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


def get_lasts():
    with shelve.open('lasts') as db:
        d = dict(db)
    return d


def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def get_lens():
    with shelve.open('lens') as db:
        d = dict(db)

    bins = list(chunks([str(n) for n in range(50)], 5))
    labels = ['<5', '5-9', '10-14', '15-19', '20-24', '25-29',
              '30-34', '35-39', '40-44', '45-49', '>50']
    data = [0 for L in labels]
    for k, v in d.items():
        for idx, row in enumerate(bins):
            if k in row:
                break
        data[idx] += v

    return OrderedDict((L, d) for L, d in zip(labels, data))


def plot_network(G, years, scale=10):
    """
    Make a networkx plot and convert to base64-encoded string.
    """
    edges = G.edges()
    weights = [G[u][v]['weight'] for u, v in edges]

    counts = [scale * nx.get_node_attributes(G, 'count')[u] for u in G.nodes()]

    params = {
        'node_size': counts,
        'with_labels': True,
        'verticalalignment': 'bottom',
        'width': weights,
    }

    pos = nx.spring_layout(G)

    fig = plt.figure(figsize=(12, 12))
    nx.draw(G, pos, **params)

    # Save as base64 string.
    handle = BytesIO()
    plt.savefig(handle, format='png', facecolor=fig.get_facecolor())
    plt.close()
    handle.seek(0)
    figdata_png = base64.b64encode(handle.getvalue())

    return figdata_png.decode('utf8')


def plot_bars(data, drop=False, sort=False, log=False, title=True, lpos=None):
    """
    Generic bar plotting function. Does all the plots.
    """
    if drop:
        _ = data.pop('undergrad', None)
        _ = data.pop('retired', None)
        _ = data.pop('unemployed', None)
        _ = data.pop('break', None)

    labels = list(data.keys())
    values = list(data.values())

    if sort:
        labels = [l for _, l in sorted(zip(values, labels), reverse=True)]
        values = sorted(values, reverse=True)

    y = list(range(len(values)))
    y_min, y_max = y[0]-0.75, y[-1]+0.75

    fig, ax = plt.subplots(figsize=(8, 8))
    _ = ax.barh(y, values, color='orange', align='center', edgecolor='none')
    ax.set_yticks(y)
    if log:
        ax.set_xscale('log')
    ax.set_yticklabels(labels, size=12)
    ax.set_ylim(y_max, y_min)  # Label top-down.
    ax.grid(c='black', alpha=0.15, which='both')
    ax.patch.set_facecolor("white")
    fig.patch.set_facecolor("none")

    if title is True:
        t = "{:.2f} person-careers of experience".format(sum(values)/40)
    elif title:
        t = title
    else:
        t = ""
    ax.set_title(t)

    if lpos is None:
        lpos = min(values)
    for i, d in enumerate(values):
        ax.text(lpos, i, "{}".format(int(d)), va='center', size=12)

    plt.tight_layout()

    # Put in memory.
    handle = BytesIO()
    plt.savefig(handle, format='png', facecolor=fig.get_facecolor())
    plt.close()

    # Encode.
    handle.seek(0)
    figdata_png = base64.b64encode(handle.getvalue()).decode('utf8')

    return figdata_png
