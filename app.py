# Many thanks to: https://wikitech.wikimedia.org/wiki/Help:Toolforge/My_first_Flask_OAuth_tool
import os
import re
import yaml

from flask import Flask, jsonify, render_template, request
from flask_cors import CORS

app = Flask(__name__)

WIKIPEDIA_LANGUAGE_CODES = ['aa', 'ab', 'ace', 'ady', 'af', 'ak', 'als', 'am', 'an', 'ang', 'ar', 'arc', 'ary', 'arz', 'as', 'ast', 'atj', 'av', 'avk', 'awa', 'ay', 'az', 'azb', 'ba', 'ban', 'bar', 'bat-smg', 'bcl', 'be', 'be-x-old', 'bg', 'bh', 'bi', 'bjn', 'bm', 'bn', 'bo', 'bpy', 'br', 'bs', 'bug', 'bxr', 'ca', 'cbk-zam', 'cdo', 'ce', 'ceb', 'ch', 'cho', 'chr', 'chy', 'ckb', 'co', 'cr', 'crh', 'cs', 'csb', 'cu', 'cv', 'cy', 'da', 'de', 'din', 'diq', 'dsb', 'dty', 'dv', 'dz', 'ee', 'el', 'eml', 'en', 'eo', 'es', 'et', 'eu', 'ext', 'fa', 'ff', 'fi', 'fiu-vro', 'fj', 'fo', 'fr', 'frp', 'frr', 'fur', 'fy', 'ga', 'gag', 'gan', 'gcr', 'gd', 'gl', 'glk', 'gn', 'gom', 'gor', 'got', 'gu', 'gv', 'ha', 'hak', 'haw', 'he', 'hi', 'hif', 'ho', 'hr', 'hsb', 'ht', 'hu', 'hy', 'hyw', 'hz', 'ia', 'id', 'ie', 'ig', 'ii', 'ik', 'ilo', 'inh', 'io', 'is', 'it', 'iu', 'ja', 'jam', 'jbo', 'jv', 'ka', 'kaa', 'kab', 'kbd', 'kbp', 'kg', 'ki', 'kj', 'kk', 'kl', 'km', 'kn', 'ko', 'koi', 'kr', 'krc', 'ks', 'ksh', 'ku', 'kv', 'kw', 'ky', 'la', 'lad', 'lb', 'lbe', 'lez', 'lfn', 'lg', 'li', 'lij', 'lld', 'lmo', 'ln', 'lo', 'lrc', 'lt', 'ltg', 'lv', 'mai', 'map-bms', 'mdf', 'mg', 'mh', 'mhr', 'mi', 'min', 'mk', 'ml', 'mn', 'mnw', 'mr', 'mrj', 'ms', 'mt', 'mus', 'mwl', 'my', 'myv', 'mzn', 'na', 'nah', 'nap', 'nds', 'nds-nl', 'ne', 'new', 'ng', 'nl', 'nn', 'no', 'nov', 'nqo', 'nrm', 'nso', 'nv', 'ny', 'oc', 'olo', 'om', 'or', 'os', 'pa', 'pag', 'pam', 'pap', 'pcd', 'pdc', 'pfl', 'pi', 'pih', 'pl', 'pms', 'pnb', 'pnt', 'ps', 'pt', 'qu', 'rm', 'rmy', 'rn', 'ro', 'roa-rup', 'roa-tara', 'ru', 'rue', 'rw', 'sa', 'sah', 'sat', 'sc', 'scn', 'sco', 'sd', 'se', 'sg', 'sh', 'shn', 'si', 'simple', 'sk', 'sl', 'sm', 'smn', 'sn', 'so', 'sq', 'sr', 'srn', 'ss', 'st', 'stq', 'su', 'sv', 'sw', 'szl', 'szy', 'ta', 'tcy', 'te', 'tet', 'tg', 'th', 'ti', 'tk', 'tl', 'tn', 'to', 'tpi', 'tr', 'ts', 'tt', 'tum', 'tw', 'ty', 'tyv', 'udm', 'ug', 'uk', 'ur', 'uz', 've', 'vec', 'vep', 'vi', 'vls', 'vo', 'wa', 'war', 'wo', 'wuu', 'xal', 'xh', 'xmf', 'yi', 'yo', 'za', 'zea', 'zh', 'zh-classical', 'zh-min-nan', 'zh-yue', 'zu']

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
#CORS(app, resources={'*': {'origins': '*'}})
CORS(app)

@app.route('/')
def index():
    lang, title, qid = validate_api_args()
    return render_template('index.html', lang=lang, title=title, qid=qid)

@app.route('/topic')
def topic():
    lang, title, qid = validate_api_args()
    return render_template('topic.html', lang=lang, title=title, qid=qid)

@app.route('/topic-comparison')
@app.route('/comparison')
def topic_comparison():
    lang, title, qid = validate_api_args()
    return render_template('comparison.html', lang=lang, title=title, qid=qid)

@app.route('/article-tagging')
def content_tagging():
    lang, title, qid = validate_api_args()
    return render_template('article-tagging.html', lang=lang, title=title, qid=qid)

@app.route('/diff-tagging')
def diff_tagging():
    lang, title, qid = validate_api_args()
    return render_template('diff-tagging.html', lang=lang, revid=title, qid=qid)

@app.route('/person')
def person():
    lang, title, qid = validate_api_args()
    return render_template('person.html', lang=lang, title=title, qid=qid)

@app.route('/countries')
def countries():
    lang, title, qid = validate_api_args()
    return render_template('countries.html', lang=lang, title=title, qid=qid)

@app.route('/quality')
def quality():
    lang, title, qid = validate_api_args()
    return render_template('quality.html', lang=lang, title=title, qid=qid)

def validate_lang(lang):
    return lang in WIKIPEDIA_LANGUAGE_CODES

def validate_qid(qid):
    return re.match('^Q[0-9]+$', qid)

def valildate_revid(revid):
    try:
        int(revid)
        return True
    except (ValueError, TypeError):
        return False

def validate_api_args():
    lang = None
    if 'lang' in request.args:
        if validate_lang(request.args['lang'].lower()):
            lang = request.args['lang'].lower()

    title = None
    if 'title' in request.args:
        title = request.args['title'].replace('_', ' ')
    elif 'revid' in request.args:
        if valildate_revid(request.args['revid']):
            title = request.args['revid']

    qid = None
    if 'qid' in request.args:
        if validate_qid(request.args['qid'].upper()):
            qid = request.args['qid'].upper()

    return lang, title, qid