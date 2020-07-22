# Many thanks to: https://wikitech.wikimedia.org/wiki/Help:Toolforge/My_first_Flask_OAuth_tool

import os
import yaml

from flask import Flask, render_template
import flask_cors

app = Flask(__name__)

__dir__ = os.path.dirname(__file__)
app.config.update(
    yaml.safe_load(open(os.path.join(__dir__, 'default_config.yaml'))))
try:
    app.config.update(
        yaml.safe_load(open(os.path.join(__dir__, 'config.yaml'))))
except IOError:
    # It is ok if there is no local config file
    pass

# Enable CORS for API endpoints
cors = flask_cors.CORS(app, resources={r'/api/*': {'origins': '*'}})

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/comparison')
def index():
    return render_template('comparison.html')