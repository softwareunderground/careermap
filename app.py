import os

from flask import Flask, request, render_template

import utils


app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def index():
    """
    Serve the form.
    """
    if request.method == 'POST':
        data = request.form.get('data')
        result = utils.store(data)
    else:
        result = ''

    return render_template('form.html', result=result)


@app.route('/plot', methods=["GET"])
def plot():
    """
    Serve a plot of the network.
    """
    scale = int(request.args.get('scale') or '10')

    log = request.args.get('log') or 'false'
    if log.lower() in ['0', 'false', 'off', 'no']:
        log = False
    else:
        log = True

    drop = request.args.get('drop') or 'false'
    if drop.lower() in ['0', 'false', 'off', 'no']:
        drop = False
    else:
        drop = True

    years = utils.get_years()
    G = utils.get_network(years)
    if len(G) < 1:
        return render_template('plot.html', result={})
    result = {'network_plot': utils.plot_network(G, years, scale=scale)}
    result['years_plot'] = utils.plot_years(years, drop=drop, log=log)
    return render_template('plot.html', result=result)


@app.route('/about', methods=['GET'])
def about():
    """
    Serve the page.
    """
    return render_template('about.html')


@app.route('/delete', methods=['DELETE'])
def delete():
    """
    Delete the database.
    """
    if request.method == 'DELETE':
        # _ = os.remove("log.txt")
        _ = os.remove("edges.db")
        _ = os.remove("nodes.db")
        return "Done"
