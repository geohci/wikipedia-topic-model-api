# Many thanks to: https://wikitech.wikimedia.org/wiki/Help:Toolforge/My_first_Flask_OAuth_tool

import os
import re
import yaml

import fasttext
from flask import Flask, request, jsonify, render_template
import flask_cors
import mwapi

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

# Wikidata API session
SESSION_WD = mwapi.Session('https://www.wikidata.org', user_agent=app.config['CUSTOM_UA'])

# load in fastText models for making predictions
try:
    FT_MODEL_WD = fasttext.load_model('models/model_wd.bin')
except Exception:
    FT_MODEL_WD = None
try:
    FT_MODEL_LA = fasttext.load_model('models/model_la.bin')
except Exception:
    FT_MODEL_LA = None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/v1/wikidata/topic', methods=['GET'])
def get_topics_wd():
    """Wikidata-based topic modeling endpoint. Makes prediction based on statements associated with Wikidata item."""
    if FT_MODEL_WD is not None:
        qid, threshold, debug, error = validate_api_args_wd()
        if error is not None:
            return jsonify({'Error': error})
        else:
            name, claims = get_wikidata_claims(qid, SESSION_WD, debug)
            topics = get_predictions(' '.join([' '.join(c) for c in claims]),
                                     FT_MODEL_WD, threshold, debug)
            topics, claims = adjust_topics_based_on_claims(topics, claims)
            if debug:
                return render_template('wikidata_topics.html',
                                       qid=qid, claims=claims, topics=topics, name=name)
            else:
                result = {'qid': qid,
                          'name': name,
                          'results': [{'topic':t[0], 'score':t[1]} for t in topics]
                          }
                return jsonify(result)
    else:
        return jsonify({'Error': 'model not available for Wikidata topic model.'})

@app.route('/api/v1/lang-agnostic-outlinks/topic', methods=['GET'])
def get_topics_la():
    """Wikipedia-based topic modeling endpoint. Makes prediction based on outlinks associated with a Wikipedia article."""
    if FT_MODEL_LA is not None:
        lang, page_title, threshold, debug, error = validate_api_args_la()
        if error is not None:
            return jsonify({'Error': error})
        else:
            outlinks = get_outlinks(page_title, lang)
            if debug:
                print(outlinks)
            topics = get_predictions(features_str=' '.join(outlinks), model=FT_MODEL_LA, threshold=threshold, debug=debug)
            if debug:
                return render_template('langagnostic_topics.html',
                                       lang=lang, outlinks=outlinks, topics=topics, page_title=page_title)
            else:
                result = {'article': 'https://{0}.wikipedia.org/wiki/{1}'.format(lang, page_title),
                          'results': [{'topic':t[0], 'score':t[1]} for t in topics]
                          }
                return jsonify(result)
    else:
        return jsonify({'Error': 'model not available for language-agnostic topic model.'})

def get_predictions(features_str, model, threshold=0.5, debug=False):
    """Get fastText model predictions for an input feature string."""
    lbls, scores = model.predict(features_str, k=-1)
    results = {l:s for l,s in zip(lbls, scores)}
    if debug:
        print(results)
    sorted_res = [(l.replace("__label__", ""), results[l]) for l in sorted(results, key=results.get, reverse=True)]
    above_threshold = [r for r in sorted_res if r[1] >= threshold]
    lbls_above_threshold = []
    if above_threshold:
        for res in above_threshold:
            if debug:
                print('{0}: {1:.3f}'.format(*res))
            if res[1] > 0.5:
                lbls_above_threshold.append(res[0])
    elif debug:
        print("No label above {0} threshold.".format(threshold))
        print("Top result: {0} ({1:.3f}) -- {2}".format(sorted_res[0][0], sorted_res[0][1], sorted_res[0][2]))

    return above_threshold

def get_outlinks(title, lang, limit=1000, session=None):
    """Gather set of up to `limit` outlinks for an article."""
    if session is None:
        session = mwapi.Session('https://{0}.wikipedia.org'.format(lang), user_agent=app.config['CUSTOM_UA'])

    # generate list of all outlinks (to namespace 0) from the article and their associated Wikidata IDs
    result = session.get(
        action="query",
        generator="links",
        titles=title,
        redirects='',
        prop='pageprops',
        ppprop='wikibase_item',
        gplnamespace=0,  # this actually doesn't seem to work :/
        gpllimit=50,
        format='json',
        formatversion=2,
        continuation=True
    )
    try:
        outlink_qids = set()
        for r in result:
            for outlink in r['query']['pages']:
                if outlink['ns'] == 0 and 'missing' not in outlink:  # namespace 0 and not a red link
                    qid = outlink.get('pageprops', {}).get('wikibase_item', None)
                    if qid is not None:
                        outlink_qids.add(qid)
            if len(outlink_qids) > limit:
                break
        return outlink_qids
    except Exception:
        return None

def get_canonical_page_title(title, lang, session=None):
    """Resolve redirects / normalization -- used to verify that an input page_title exists"""
    if session is None:
        session = mwapi.Session('https://{0}.wikipedia.org'.format(lang), user_agent=app.config['CUSTOM_UA'])

    result = session.get(
        action="query",
        prop="info",
        inprop='',
        redirects='',
        titles=title,
        format='json',
        formatversion=2
    )
    print(result)
    if 'missing' in result['query']['pages'][0]:
        return None
    else:
        return result['query']['pages'][0]['title']

def get_qid(title, lang, session=None):
    """Get Wikidata item ID for a given Wikipedia article"""
    if session is None:
        session = mwapi.Session('https://{0}.wikipedia.org'.format(lang), user_agent=app.config['CUSTOM_UA'])

    try:
        result = session.get(
            action="query",
            prop="pageprops",
            ppprop='wikibase_item',
            titles=title,
            format='json',
            formatversion=2
        )
    except Exception:
        return "API call failed for {0}.wikipedia: {1}".format(lang, title)

    try:
        return result['query']['pages'][0]['pageprops'].get('wikibase_item', None)
    except (KeyError, IndexError):
        return "Title does not exist in {0}: {1}".format(lang, title)

def get_wikidata_claims(qid, session, debug=False):
    """Get list of claims associated with a Wikidata item."""
    # default results
    name = ""
    claims_tuples = []

    # get claims for wikidata item
    result = {}
    try:
        result = session.get(
            action="wbgetentities",
            props='claims|labels',
            languages='en',
            languagefallback='',
            format='json',
            ids=qid
        )
    except Exception:
        pass
    if debug:
        print(result)

    if 'missing' not in result['entities'][qid]:
        # get best label
        for lbl in result['entities'][qid]['labels']:
            name = result['entities'][qid]['labels'][lbl]['value']
            break

        # convert claims to fastText bag-of-words format
        claims = result['entities'][qid]['claims']
        for prop in claims:  # each property, such as P31 instance-of
            included = False
            for statement in claims[prop]:  # each value under that property -- e.g., instance-of might have three different values
                try:
                    if statement['type'] == 'statement' and statement['mainsnak']['datatype'] == 'wikibase-item':
                        claims_tuples.append((prop, statement['mainsnak']['datavalue']['value']['id']))
                        included = True
                except Exception:
                    continue
            if not included:
                claims_tuples.append((prop, ))
        if not len(claims_tuples):
            claims_tuples = [('<NOCLAIM>', )]
        if debug:
            print(claims_tuples)

    return name, claims_tuples

def validate_api_args_la():
    """Validate API arguments for language-agnostic model."""
    error = None
    lang = None
    page_title = None
    threshold = 0.5
    if request.args.get('title') and request.args.get('lang'):
        lang = request.args['lang']
        page_title = get_canonical_page_title(request.args['title'], lang)
        if page_title is None:
            error = 'no matching article for <a href="https://{0}.wikipedia.org/wiki/{1}">https://{0}.wikipedia.org/wiki/{1}</a>'.format(lang, request.args['title'])
    elif request.args.get('lang'):
        error = 'missing an article title -- e.g., "2005_World_Series" for <a href="https://en.wikipedia.org/wiki/2005_World_Series">https://en.wikipedia.org/wiki/2005_World_Series</a>'
    elif request.args.get('title'):
        error = 'missing a language -- e.g., "en" for English'
    else:
        error = 'missing language -- e.g., "en" for English -- and title -- e.g., "2005_World_Series" for <a href="https://en.wikipedia.org/wiki/2005_World_Series">https://en.wikipedia.org/wiki/2005_World_Series</a>'

    if 'threshold' in request.args:
        try:
            threshold = float(request.args['threshold'])
        except ValueError:
            threshold = "Error: threshold value provided not a float: {0}".format(request.args['threshold'])

    debug = False
    if 'debug' in request.args:
        debug = True
        threshold = 0

    return lang, page_title, threshold, debug, error

def validate_qid(qid):
    """Make sure QID string is expected format."""
    return re.match('^Q[0-9]+$', qid)

def validate_api_args_wd():
    """Validate API arguments for Wikidata-based model."""
    error = None
    qid = None
    if 'qid' in request.args:
        qid = request.args['qid'].upper()
        if not validate_qid(qid):
            error = "Error: poorly formatted 'qid' field. {0} does not match 'Q#...'".format(qid)
    elif 'title' in request.args and 'lang' in request.args:
        qid = get_qid(request.args['title'], lang=request.args['lang'])
        if not validate_qid(qid):
            error = qid
    else:
        error = "Error: no 'qid' or 'lang'+'title' field provided. Please specify."

    threshold = 0.5
    if 'threshold' in request.args:
        try:
            threshold = float(request.args['threshold'])
        except ValueError:
            threshold = "Error: threshold value provided not a float: {0}".format(request.args['threshold'])

    debug = False
    if 'debug' in request.args:
        debug = True
        threshold = 0

    return qid, threshold, debug, error

def adjust_topics_based_on_claims(topics, claims):
    """Make several post-prediction corrections to Wikidata-based model using rules + claims data."""
    joined_claims = [":".join(c) for c in claims]
    properties = [c[0] for c in claims]
    # list / disambiguation pages
    if 'P31:Q4167410' in joined_claims:
        topics = [('Compilation.List_Disambig', 1)] + topics
    elif 'P31:Q13406463' in joined_claims:
        topics = [('Compilation.List_Disambig', 1)] + topics
    elif 'P360' in properties:
        topics = [('Compilation.List_Disambig', 1)] + topics
    # geography only should apply to items with coordinates
    if 'P625' not in joined_claims:
        for idx in range(len(topics)):
            if topics[idx][0].startswith('Geography'):
                topics[idx] = (topics[idx][0], max(0, topics[idx][1] - 0.501))
    # Culture.Biography.Women should not include men (at 0.5 threshold):
    if ('P21:Q6581097' in joined_claims or  # male
            'P21:Q2449503' in joined_claims or  # transgender male
            'P21:Q44148' in joined_claims or  # male organisms
            'P21:Q27679766' in joined_claims or  # transmasculine
            'P21:Q15145778' in joined_claims):  # cisgender male
        for idx in range(len(topics)):
            if topics[idx][0] == 'Culture.Biography.Women':
                topics[idx] = (topics[idx][0], min(0.49, topics[idx][1]))
    topics = sorted(topics, key=lambda tup: tup[1], reverse=True)
    return topics, claims