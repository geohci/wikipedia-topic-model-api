# Many thanks to: https://wikitech.wikimedia.org/wiki/Help:Toolforge/My_first_Flask_OAuth_tool
import json
import math
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

@app.route('/topic-prototype')
def topic_prototype():
    lang, title, qid = validate_api_args()
    return render_template('topic-prototype.html', lang=lang, title=title, qid=qid)

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
    

@app.route('/maybe-add-this')
def recommend_things():
    lang = None
    if 'lang' in request.args:    
        lang = request.args['lang'].lower()

    title = None
    if 'title' in request.args:
        title = request.args['title'].replace('_', ' ')
    elif 'page_title' in request.args:
        title = request.args['page_title'].replace('_', ' ')
    
    rec_type = None
    if 'rec_type' in request.args:
        rec_type = request.args['rec_type']

    match_io = False
    pages_to_check = 10
    if 'strict' in request.args:
        match_io = True
        pages_to_check = 20


    if lang and title and rec_type:
        # https://en.wikipedia.org/w/api.php?action=query&generator=search&format=json&gsrnamespace=0&gsrwhat=text&gsrsearch=morelike:Wayne_McDaniel&prop=categories&clprop=hidden&cllimit=max
        base_url = f"https://{lang}.wikipedia.org/w/api.php"
        params = {"action":"query",
                  "generator":"search",
                  "gsrnamespace":0,
                  "gsrwhat":"text",
                  "gsrsearch":f"morelike:{title}", 
                  "gsrlimit":pages_to_check,                 
                  "format":"json",
                  "formatversion":2
                  }
        if rec_type == 'categories':
            params["prop"] = "categories"
            params["cllimit"] = "max"
            params["clshow"] = "!hidden"
            generator_fn = page_to_categories
        elif rec_type == 'templates':
            params["prop"] = "templates"
            params["tlnamespace"] = 10
            params["tllimit"] = "max"
            generator_fn = page_to_templates
        elif rec_type == 'sections':
            params["prop"] = "revisions"
            params["rvprop"] = "content"
            params["rvslots"] = "main"
            generator_fn = page_to_sections

        pids_to_keep = get_similar_articles(title, lang, limit=20) if match_io else None

        response = requests.get(base_url, params=params, headers={'User-Agent': app.config['CUSTOM_UA']})
        entity_counts = {}
        pages_checked = []
        for page in response.json().get("query", {}).get("pages", []):
            if not pids_to_keep or page['pageid'] in pids_to_keep:
                pages_checked.append(page['title'])
                for entity in generator_fn(page):
                    entity_counts[entity] = entity_counts.get(entity, 0) + 1

        entity_counts = {e:count for e,count in entity_counts.items() if count > 1}

        for k in ['generator', 'gsrnamespace', 'gsrwhat', 'gsrsearch', 'gsrlimit']:
            params.pop(k)
        params['titles'] = title.replace("_", " ")
        try:
            response = requests.get(base_url, params=params, headers={'User-Agent': app.config['CUSTOM_UA']}).json()
            groundtruth = set([e for e in generator_fn(response["query"]["pages"][0])])
        except Exception:
            groundtruth = set()
            
        if rec_type == 'categories':
            overall_usage = category_idf(list(entity_counts.keys()), lang)
            # https://en.wikipedia.org/w/api.php?action=query&meta=siteinfo&siprop=statistics&format=json&formatversion=2
            base_url = f"https://{lang}.wikipedia.org/w/api.php"
            params = {"action":"query",
                      "meta":"siteinfo",
                      "siprop":"statistics",
                      "format":"json",
                      "formatversion":2
                      }
            response = requests.get(base_url, params=params, headers={'User-Agent': app.config['CUSTOM_UA']})
            total_page_count = response.json().get("query", {}).get("statistics", {}).get("articles", 0)
            sort_key = 'tf-idf'
        elif rec_type == "templates":
            # TODO: this takes forever because so many templates and each call can be kinda slow -- trim maybe somehow?
            overall_usage = template_idf([t for t in entity_counts if entity_counts[t] > 1], lang)
            # https://en.wikipedia.org/w/api.php?action=query&meta=siteinfo&siprop=statistics&format=json&formatversion=2
            base_url = f"https://{lang}.wikipedia.org/w/api.php"
            params = {"action":"query",
                      "meta":"siteinfo",
                      "siprop":"statistics",
                      "format":"json",
                      "formatversion":2
                      }
            response = requests.get(base_url, params=params, headers={'User-Agent': app.config['CUSTOM_UA']})
            total_page_count = response.json().get("query", {}).get("statistics", {}).get("articles", 0)
            sort_key = 'tf-idf'
        else:
            # sections -- tfidf both essentially impossible and way less useful so skip
            overall_usage = {}
            total_page_count = 0
            sort_key = 'pages-using'

        recommendations = []
        for e in sorted(entity_counts, key=entity_counts.get, reverse=True):
            term_count = entity_counts[e]
            tf = term_count / len(pages_checked)
            doc_count = overall_usage.get(e)
            try:
                document_frequency = doc_count / total_page_count
                idf = math.log10(1 / document_frequency)
            except Exception:
                idf = 0
            recommendations.append({'rec':e, 'pages-using':term_count, 'tf-idf':tf * idf, 'already-present': e in groundtruth})

        recommendations = sorted(recommendations, key=lambda x: x[sort_key], reverse=True)

        result = {'lang':lang, 'title':title, 'rec-type':rec_type, 'pages-checked':pages_checked,
                  'recommendations': recommendations}

        return jsonify(result)
    else:
        return jsonify({"error": f"missing lang, title, or rec_type (categories, templates, sections)"})
    
def get_similar_articles(title, lang, limit=20):
    """Gather set of up to `limit` links for an article."""

    base_url = f"https://{lang}.wikipedia.org/w/api.php"
    params = {
        'action': "query",
        'prop': "pageprops",
        'ppprop': 'wikibase_item',
        'redirects': '',
        'titles': title,
        'format': 'json',
        'formatversion': 2 
    }
    result = requests.get(base_url, params=params, headers={'User-Agent': app.config['CUSTOM_UA']}).json()
        
    if 'missing' in result['query']['pages'][0]:
        return None
    
    qid = result['query']['pages'][0].get('pageprops', {}).get('wikibase_item')
    if not qid:
        return None
    article_ios = get_p31(qid)
    if not article_ios:
        return None
    base_url = f"https://{lang}.wikipedia.org/w/api.php"
    params = {
            "action": "query",
            "generator": "search",
            "titles": title,
            "redirects": '',
            "prop": "pageprops",
            "ppprop": "wikibase_item",
            "gsrwhat": "text",
            "gsrnamespace": 0,
            "gsrsearch": f"morelike:{title}",
            "gsrlimit": limit,
            "format": 'json',
            "formatversion": 2
    }
    result = requests.get(base_url, params=params, headers={'User-Agent': app.config['CUSTOM_UA']}).json()

    pids_to_keep = set()
    try:
        for link in result['query']['pages']:
            if link['ns'] == 0 and 'missing' not in link:  # namespace 0 and not a red link
                qid = link.get('pageprops', {}).get('wikibase_item')
                if qid:
                    morelike_ios = get_p31(qid)
                    if article_ios.intersection(morelike_ios):
                        pid = link['pageid']
                        pids_to_keep.add(pid)
    except Exception:
        return None
    return pids_to_keep


def get_p31(qid):
    # https://www.wikidata.org/w/api.php?action=wbgetclaims&entity=Q2479913&property=P31&format=json&formatversion=2&props
    base_url = "https://www.wikidata.org/w/api.php"
    params = {
        'action': "wbgetclaims",
        'entity': qid,
        'property': 'P31',
        'format': 'json',
        'formatversion': 2
    }
    result = requests.get(base_url, params=params, headers={'User-Agent': app.config['CUSTOM_UA']}).json()
    instance_ofs = set()
    try:
        for claim in result['claims']['P31']:
            io = claim['mainsnak']['datavalue']['value']['id']
            if io:
                instance_ofs.add(io)
        return instance_ofs
    except Exception:
        return instance_ofs


    
def page_to_categories(page):
    for cat in page.get('categories', []):
        yield cat['title']

def page_to_templates(page):
    for temp in page.get('templates', []):
        if '/' not in temp["title"]:
            yield temp['title']

def page_to_sections(page):
    try:
        wikitext = page['revisions'][0]['slots']['main']['content']
        for heading in re.findall('={2,}(.*?)={2,}', wikitext):
            yield heading.strip()
    except Exception:
        pass

def category_idf(categories, lang):
    # category usage: https://en.wikipedia.org/w/api.php?action=query&prop=categoryinfo&titles=Category:Ships_built_in_Kiel|Category:Ships_built_in_Germany&format=json&formatversion=2
    base_url = f"https://{lang}.wikipedia.org/w/api.php"
    categories_per_api_call = 50
    category_count = {}
    for i in range(0, len(categories), categories_per_api_call):
        params = {"action":"query",
                  "prop":"categoryinfo",
                  "titles":"|".join(categories[i:i+categories_per_api_call]),
                  "format":"json",
                  "formatversion":2
                  }
        
        response = requests.get(base_url, params=params, headers={'User-Agent': app.config['CUSTOM_UA']})
        for page in response.json().get("query", {}).get("pages", []):
            category = page.get('title')
            pages = page.get('categoryinfo', {}).get('pages', 0)
            subcats = page.get('categoryinfo', {}).get('subcats', 0)
            # prefer categories with fewer subcategories -- i.e. maximally specific
            count = pages * (subcats + 1)
            category_count[category] = count

    return category_count

def template_idf(templates, lang):
    # template usage: https://linkcount.toolforge.org/api/?page=Template:Infobox_body_of_water&project=en.wikipedia.org&namespaces=0
    base_url = "https://linkcount.toolforge.org/api/"
    template_count = {}
    for t in templates:
        params = {"page":t,
                  "project":f"{lang}.wikipedia.org",
                  "namespaces":0
                  }
        response = requests.get(base_url, params=params, headers={'User-Agent': app.config['CUSTOM_UA']}).json()
        # we want both direct and indirect (via redirects)
        template_count[t] = response.get('transclusions', {}).get('all', 0)

    return template_count