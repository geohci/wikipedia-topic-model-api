# Many thanks to: https://wikitech.wikimedia.org/wiki/Help:Toolforge/My_first_Flask_OAuth_tool
import gzip
import os
import re
from urllib.request import urlretrieve
import yaml

from flask import Flask, jsonify, render_template, request
from flask_cors import CORS

app = Flask(__name__)

WIKIPEDIA_LANGUAGE_CODES = ['aa', 'ab', 'ace', 'ady', 'af', 'ak', 'als', 'am', 'an', 'ang', 'ar', 'arc', 'ary', 'arz', 'as', 'ast', 'atj', 'av', 'avk', 'awa', 'ay', 'az', 'azb', 'ba', 'ban', 'bar', 'bat-smg', 'bcl', 'be', 'be-x-old', 'bg', 'bh', 'bi', 'bjn', 'bm', 'bn', 'bo', 'bpy', 'br', 'bs', 'bug', 'bxr', 'ca', 'cbk-zam', 'cdo', 'ce', 'ceb', 'ch', 'cho', 'chr', 'chy', 'ckb', 'co', 'cr', 'crh', 'cs', 'csb', 'cu', 'cv', 'cy', 'da', 'de', 'din', 'diq', 'dsb', 'dty', 'dv', 'dz', 'ee', 'el', 'eml', 'en', 'eo', 'es', 'et', 'eu', 'ext', 'fa', 'ff', 'fi', 'fiu-vro', 'fj', 'fo', 'fr', 'frp', 'frr', 'fur', 'fy', 'ga', 'gag', 'gan', 'gcr', 'gd', 'gl', 'glk', 'gn', 'gom', 'gor', 'got', 'gu', 'gv', 'ha', 'hak', 'haw', 'he', 'hi', 'hif', 'ho', 'hr', 'hsb', 'ht', 'hu', 'hy', 'hyw', 'hz', 'ia', 'id', 'ie', 'ig', 'ii', 'ik', 'ilo', 'inh', 'io', 'is', 'it', 'iu', 'ja', 'jam', 'jbo', 'jv', 'ka', 'kaa', 'kab', 'kbd', 'kbp', 'kg', 'ki', 'kj', 'kk', 'kl', 'km', 'kn', 'ko', 'koi', 'kr', 'krc', 'ks', 'ksh', 'ku', 'kv', 'kw', 'ky', 'la', 'lad', 'lb', 'lbe', 'lez', 'lfn', 'lg', 'li', 'lij', 'lld', 'lmo', 'ln', 'lo', 'lrc', 'lt', 'ltg', 'lv', 'mai', 'map-bms', 'mdf', 'mg', 'mh', 'mhr', 'mi', 'min', 'mk', 'ml', 'mn', 'mnw', 'mr', 'mrj', 'ms', 'mt', 'mus', 'mwl', 'my', 'myv', 'mzn', 'na', 'nah', 'nap', 'nds', 'nds-nl', 'ne', 'new', 'ng', 'nl', 'nn', 'no', 'nov', 'nqo', 'nrm', 'nso', 'nv', 'ny', 'oc', 'olo', 'om', 'or', 'os', 'pa', 'pag', 'pam', 'pap', 'pcd', 'pdc', 'pfl', 'pi', 'pih', 'pl', 'pms', 'pnb', 'pnt', 'ps', 'pt', 'qu', 'rm', 'rmy', 'rn', 'ro', 'roa-rup', 'roa-tara', 'ru', 'rue', 'rw', 'sa', 'sah', 'sat', 'sc', 'scn', 'sco', 'sd', 'se', 'sg', 'sh', 'shn', 'si', 'simple', 'sk', 'sl', 'sm', 'smn', 'sn', 'so', 'sq', 'sr', 'srn', 'ss', 'st', 'stq', 'su', 'sv', 'sw', 'szl', 'szy', 'ta', 'tcy', 'te', 'tet', 'tg', 'th', 'ti', 'tk', 'tl', 'tn', 'to', 'tpi', 'tr', 'ts', 'tt', 'tum', 'tw', 'ty', 'tyv', 'udm', 'ug', 'uk', 'ur', 'uz', 've', 'vec', 'vep', 'vi', 'vls', 'vo', 'wa', 'war', 'wo', 'wuu', 'xal', 'xh', 'xmf', 'yi', 'yo', 'za', 'zea', 'zh', 'zh-classical', 'zh-min-nan', 'zh-yue', 'zu']
MISALIGNMENT = {}
TOPIC_LBLS = {}

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

@app.route('/comparison')
def comparison():
    lang, title, qid = validate_api_args()
    return render_template('comparison.html', lang=lang, title=title, qid=qid)

@app.route('/countries')
def countries():
    lang, title, qid = validate_api_args()
    return render_template('countries.html', lang=lang, title=title, qid=qid)

@app.route('/misalignment')
def misalignment():
    langs = '|'.join([lang for lang in request.args.get('lang', '').lower().split('|') if validate_lang(lang)])
    return render_template('misalignment.html', lang=langs)

@app.route('/misalignment/api/v1/topic')
def misalignment_api():
    langs = [lang for lang in request.args.get('lang', '').lower().split('|') if validate_lang(lang)][:6]
    results = []
    for t in sorted(MISALIGNMENT):
        results.append({'topic':t, 'topic-display':TOPIC_LBLS[t], 'data':{l:{'num_articles':MISALIGNMENT[t][l][0], 'misalignment':f'{MISALIGNMENT[t][l][1]:.3f}'} for l in langs}})
    return jsonify({'langs':langs, 'results':results})


def validate_lang(lang):
    return lang in WIKIPEDIA_LANGUAGE_CODES

def validate_qid(qid):
    return re.match('^Q[0-9]+$', qid)

def validate_api_args():
    lang = None
    if 'lang' in request.args:
        if validate_lang(request.args['lang'].lower()):
            lang = request.args['lang'].lower()

    title = None
    if 'title' in request.args:
        title = request.args['title'].replace('_', ' ')

    qid = None
    if 'qid' in request.args:
        if validate_qid(request.args['qid'].upper()):
            qid = request.args['qid'].upper()

    return lang, title, qid

def load_misalignment_data():
    misalignment_url = 'https://analytics.wikimedia.org/published/datasets/one-off/isaacj/misalignment/misalignment-by-wiki-topic.tsv.gz'
    misalignment_fn = misalignment_url.split('/')[-1]
    if not os.path.exists(misalignment_fn):
        urlretrieve(misalignment_url, misalignment_fn)
    expected_header = ['topic', 'wiki_db', 'num_articles', 'avg_misalignment', 'topic-display']
    topic_idx = expected_header.index('topic')
    wiki_idx = expected_header.index('wiki_db')
    count_idx = expected_header.index('num_articles')
    mis_idx = expected_header.index('avg_misalignment')
    top_lbl_idx = expected_header.index('topic-display')
    wikis = set()
    with gzip.open(misalignment_fn, 'rt') as fin:
        header = next(fin).strip().split('\t')
        assert header == expected_header
        for line in fin:
            line = line.strip().split('\t')
            wiki = line[wiki_idx]
            wikis.add(wiki)
            topic = line[topic_idx]
            topic_lbl = line[top_lbl_idx]
            TOPIC_LBLS[topic] = topic_lbl
            if topic not in MISALIGNMENT:
                MISALIGNMENT[topic] = {}
            count = int(line[count_idx])
            mis = float(line[mis_idx])
            MISALIGNMENT[topic][wiki] = (count, mis)

    for topic in MISALIGNMENT:
        for w in wikis:
            if w not in MISALIGNMENT[topic]:  # possibly define a minimum sample size here too -- e.g., 30
                MISALIGNMENT[topic][w] = (0, '--')

load_misalignment_data()