import json
import os
from flask import Flask, make_response
from flask_cors import CORS

from cltk.corpus.greek.beta_to_unicode import Replacer

parse_beta = Replacer().beta_code

app = Flask(__name__)
CORS(app)

def flatten_line(line):
    if type(line) is dict:
        return line['#text']
    else:
        return line

def load_odyssey(book=None, lines=None):
    path = os.environ['HOMER_PATH']
    odyssey_file_handle = open(path + '/hom.od_gk.xml.json')
    odyssey_dict = json.load(odyssey_file_handle)

    res = odyssey_dict['TEI.2']['text']['body']['div1']

    if book and lines:
        return flatten_line([res[book - 1]['l'][line]])
    elif book:
        return [
            parse_beta(flatten_line(x).upper()) for x in res[book - 1]['l']
        ]
    else:
        return res

@app.route('/')
def root():
    return 'Welcome, to Flask!'

@app.route('/book/<int:book>')
def get_book(book):
    data = json.dumps({
        'book': {
            'no': book,
            'lines': load_odyssey(book)
        }
    })
    resp = make_response(data, 200)
    resp.headers['Content-Type'] = 'application/json'
    return resp

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
    resp = make_response(data, 200)
    resp.headers['Content-Type'] = 'application/json'
    return resp

if __name__ == "__main__":
    app.run()
