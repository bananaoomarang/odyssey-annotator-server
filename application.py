import json
import os
from flask import Flask, make_response, request
from flask_cors import CORS
from cltk.corpus.greek.beta_to_unicode import Replacer

import db

parse_beta = Replacer().beta_code

app = Flask(__name__)
CORS(app)

def flatten_line(line):
    if type(line) is dict:
        return line['#text']
    else:
        return line

def load_odyssey(book=None, lines=None, lang="gk"):
    path = os.environ['HOMER_PATH']
    odyssey_file_handle = open(path + '/hom.od_%s.xml.json' % lang)
    odyssey_dict = json.load(odyssey_file_handle)

    res = odyssey_dict['TEI.2']['text']['body']['div1']

    if lang == "gk":
        if book and lines:
            return flatten_line([res[book - 1]['l'][line]])
        elif book:
            return [
                parse_beta(flatten_line(x).upper()) for x in res[book - 1]['l']
            ]
        else:
            return res
    else:
        return res[book - 1]['p']['#text']

def handlePostInteractions():
    post_data = request.get_json()
    interaction = db.create_interaction(typee=post_data["type"], fromm=post_data["from"], to=post_data["to"], sel=post_data["selection"], book=int(post_data["book"]))
    data = json.dumps(interaction._store)
    res = make_response(data, 200)
    return res

def handleGetInteractions():
    book = request.args.get("book")
    
    if(book != None):
        book = int(book)
    
    interactions = db.fetch_interactions(book=book)
    interactions = [x for x in interactions];
    for x in interactions:
        del x['_key']
        del x['_rev']
        del x['selection']['from_offset']
        del x['selection']['to_offset']
        x['_id'] = x['_id'].replace('Interactions/', '')
        x['_from'] = x['_from'].replace('Entities/', '')
        x['_to'] = x['_to'].replace('Entities/', '')
    
    data = json.dumps(interactions)
    res = make_response(data, 200)
    return res

def handlePostEntities():
    post_data = request.get_json()
    entity = db.create_entity(name=post_data["name"], metadata=post_data["metadata"], typee=post_data["type"])
    data = json.dumps(entity._store)
    res = make_response(data, 200)
    return res

def handleGetEntities():
    entities = db.db["Entities"].fetchAll(rawResults=True)
    entities = [x for x in entities]
    for x in entities:
        x['_id'] = x['_id'].replace('Entities/', '')
    data = json.dumps([x for x in entities])
    res = make_response(data, 200)
    return res

@app.route('/')
def root():
    return 'Welcome, to Flask!'

@app.route('/book/<int:book>')
def get_book(book):
    data = json.dumps({
        'no': book,
        'greek': {
            'lines': load_odyssey(book=book, lang="gk")
        },
        'english': {
            'text': load_odyssey(book=book, lang="eng")
        }
    })
    res = make_response(data, 200)
    res.headers['Content-Type'] = 'application/json'
    return res

@app.route('/book/<int:book>/lines/<lines>')
def get_book_line(book, lines):
    line_from = lines.split('-')[0]
    line_to   = lines.split('-')[1]

    data = json.dumps({
        'book': {
            book_no: book,
            line_no: lines,
            lines: load_odyssey(book, [line_from, line_to])
        }
    })
    res = make_response(data, 200)
    res.headers['Content-Type'] = 'application/json'
    return res

@app.route('/linenos')
def get_line_nos():
    the_odyssey = load_odyssey();
    line_nos = [len(x['l']) for x in the_odyssey]

    data = json.dumps(line_nos)
    res = make_response(data, 200)
    res.headers['Content-Type'] = 'application/json'
    return res

@app.route('/interactions', methods=['GET', 'POST'])
def interactions():
    if request.method == 'POST':
        return handlePostInteractions()
    else:
        return handleGetInteractions()
    
@app.route('/entities', methods=['GET', 'POST'])
def entities():
    if request.method == 'POST':
        return handlePostEntities()
    else:
        return handleGetEntities()

@app.route('/entities/bridges')
def get_bridges():
    bridges = db.fetch_bridges()
    data = json.dumps([x for x in bridges])
    res = make_response(data, 200)

    return res

@app.route('/entities/closenesses')
def get_closeness():
    closenesses = db.get_closenesses()
    data = json.dumps(closenesses)
    res = make_response(data, 200)

    return res

@app.route('/percentdone')
def get_percent_done():
    interactions = [x for x in db.fetch_interactions()]

    max_book = max([x['book'] for x in interactions])
    max_line = max([x['selection']['to_line'] for x in interactions if x['book'] == max_book])

    the_odyssey = load_odyssey();
    line_nos = [len(x['l']) for x in the_odyssey]
    total_lines = sum(line_nos)
    total_done_lines = sum(line_nos[0:max_book]) - max_line
    
    data = json.dumps({
        'percent': (total_done_lines / total_lines) * 100,
        'stats': {
            'current_book': max_book,
            'books_left': 24 - max_book,
            'lines_left': total_lines - total_done_lines,
            'lines_left_in_current_book': line_nos[max_book-1] - max_line,
            'total_interactions': len(interactions)
        }
    })
    res = make_response(data, 200)
    return res


if __name__ == "__main__":
    app.run()
