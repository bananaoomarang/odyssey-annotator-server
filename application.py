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
    book = int(request.args.get("book"))
    interactions = db.fetch_interactions(book=book)
    data = json.dumps([x for x in interactions])
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

if __name__ == "__main__":
    app.run()
