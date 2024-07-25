# Many thanks to: https://wikitech.wikimedia.org/wiki/Help:Toolforge/My_first_Flask_OAuth_tool
import json
import os
import random
import re
import yaml

from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
import requests

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

@app.route('/html-parsing')
def html_parsing():
    lang, title, qid = validate_api_args()
    return render_template('html-parsing.html', lang=lang, title=title, qid=qid)

@app.route('/diff-tagging')
def diff_tagging():
    lang, title, qid = validate_api_args()
    return render_template('diff-tagging.html', lang=lang, revid=title, qid=qid)

@app.route('/diff-tagging-debug')
def diff_tagging_debug():
    lang, title, qid = validate_api_args()
    return render_template('diff-tagging-tmp.html', lang=lang, revid=title, qid=qid)

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
    elif 'page_title' in request.args:
        title = request.args['page_title'].replace('_', ' ')
    elif 'revid' in request.args:
        if valildate_revid(request.args['revid']):
            title = request.args['revid']

    qid = None
    if 'qid' in request.args:
        if validate_qid(request.args['qid'].upper()):
            qid = request.args['qid'].upper()

    return lang, title, qid

@app.route('/wikiproject-topic')
def wikiproject_topic():
    _, _, qid = validate_api_args()

    wikibase_url = "https://www.wikidata.org/w/api.php"
    # https://www.wikidata.org/w/api.php?action=wbgetclaims&entity=Q15304953&property=P921&format=json&formatversion=2
    main_subject_params = {"action":"wbgetclaims",
                           "entity":qid,
                           "property":"P921",
                           "format":"json",
                           "formatversion":2
                           }
    response = requests.get(wikibase_url, params=main_subject_params, headers={'User-Agent': app.config['CUSTOM_UA']})
    claims = response.json().get("claims", {}).get("P921", [])
    main_subjects = []
    for claim in claims:
        claim_value = claim.get("mainsnak", {}).get("datavalue", {}).get("value", {}).get("id", "")
        if validate_qid(claim_value):
            main_subjects.append(claim_value)

    if main_subjects:
        print(main_subjects)
        # https://www.wikidata.org/w/api.php?action=wbgetentities&ids=Q385967&props=sitelinks&format=json&formatversion=2
        sitelinks_params = {"action":"wbgetentities",
                            "ids":"|".join(main_subjects),
                            "property":"P921",
                            "format":"json",
                            "formatversion":2}
        response = requests.get(wikibase_url, params=sitelinks_params, headers={'User-Agent': app.config['CUSTOM_UA']})
        pages = []
        pages_per_ms = 5  # keep at most 5 per main subject
        wikis_to_skip = {"commonswiki", "metawiki", "wikidatawiki"}
        entities = response.json().get("entities", {})
        for item in entities:
            item_pages = {}
            for wiki in entities[item].get("sitelinks", {}):
                if wiki.endswith("wiki") and wiki not in wikis_to_skip:
                    lang = wiki.replace("wiki", "")
                    title = entities[item]["sitelinks"][wiki].get("title")
                    if lang and title:
                        item_pages[lang] = title
            if len(item_pages) > pages_per_ms:
                to_keep = list(item_pages)
                random.shuffle(to_keep)
                # sets to True if English not available (so don't need to manually add it)
                # otherwise will be False if English available and not randomly added in
                # the next for loop.
                en_included = 'en' not in item_pages
                for lang in to_keep[:pages_per_ms]:
                    pages.append((lang, item_pages[lang]))
                    if lang == 'en':
                        en_included = True
                # if english was available but not included, switch it in
                if not en_included:
                    pages[-1] = ('en', item_pages['en'])
            else:
                for lang, title in item_pages.items():
                    pages.append((lang, title))

        if pages:
            print(pages)
            inference_url = 'https://api.wikimedia.org/service/lw/inference/v1/models/outlink-topic-model:predict'
            headers = {
                    'Api-User-Agent': app.config['CUSTOM_UA'],
                    'Content-type': 'application/json'
                }
            topics = {}
            num_predictions = 0
            for lang, title in pages:
                data = {"page_title": title.replace(" ", "_"), "lang": lang, "threshold":0.0}
                try:
                    response = requests.post(inference_url, headers=headers, data=json.dumps(data)).json()
                    print(response)
                    predictions = response.get("prediction", {}).get("results", [])
                    if predictions:
                        num_predictions += 1
                        for topic in predictions:
                            topics[topic["topic"]] = topics.get(topic["topic"], 0) + topic["score"]
                except Exception:
                    continue

            results = []
            threshold = 0
            for t in sorted(topics, key=topics.get, reverse=True):
                average_score = topics[t] / num_predictions
                if average_score >= threshold:
                    results.append({t:average_score})
                else:
                    break
            return jsonify(results)
        
        else:
            return jsonify({"error": f"No Wikipedia articles for the following main subjects: {', '.join([f'https://www.wikidata.org/wiki/{q}' for q in main_subjects])}"})
    
    else:
        return jsonify({"error": f"no main subjects for https://www.wikidata.org/wiki/{qid}#P921"})