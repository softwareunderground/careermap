import os

from flask import Flask, request, render_template, make_response

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

    drop = request.args.get('drop') or 'true'
    if drop.lower() in ['1', 'true', 'on', 'yes']:
        drop = True
    else:
        drop = False

    years = utils.get_years()
    G = utils.get_network(years)
    if len(G) < 1:
        return render_template('plot.html', result={})
    result = {'network_plot': utils.plot_network(G, years, scale=scale)}

    result['years_plot'] = utils.plot_bars(years, sort=True, drop=drop, log=log)

    lasts = utils.get_lasts()
    result['lasts_plot'] = utils.plot_bars(lasts, title="Current position")

    lens = utils.get_lens()
    result['lens_plot'] = utils.plot_bars(lens, title="Career length so far", lpos=0.5)

    return render_template('plot.html', result=result)


@app.route('/about', methods=['GET'])
def about():
    """
    Serve the page.
    """
    return render_template('about.html')


@app.route('/data', methods=['GET'])
def data():
    """
    Serve the log file.
    """
    with open('log.txt') as f:
        data = f.read()
    response = make_response(data, 200)
    response.mimetype = "text/plain"
    return response


@app.route('/delete', methods=['DELETE'])
def delete():
    """
    Delete the database.
    """
    if request.method == 'DELETE':
        # _ = os.remove("log.txt")  # Keep this
        _ = os.remove("edges.db")
        _ = os.remove("nodes.db")
        _ = os.remove("lasts.db")
        _ = os.remove("lens.db")
        return "Done"
