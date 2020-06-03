from io import BytesIO
import base64

from flask import Flask, request, render_template, jsonify
from PIL import Image

import utils


app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def index():
    """
    Serve the form.
    """
    if request.method == 'POST':
        data = request.form.get('data')
        _ = utils.store_entry(data)  # Persist.
        path = utils.get_path(data)
        result = utils.store_path(path)
    else:
        result = ''

    return render_template('form.html', result=result)


@app.route('/plot', methods=["GET"])
def plot():
    """
    Serve a plot of the network.
    """
    G = utils.get_network()
    result = {'plot': utils.plot(G)}
    return render_template('plot.html', result=result)


@app.route('/about', methods=['GET'])
def about():
    """
    Serve the page.
    """
    return render_template('about.html')
