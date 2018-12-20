import re

from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy

from wtforms import Form, BooleanField, StringField, RadioField

app = Flask(__name__)
con = 'mysql+pymysql://root:12345678@localhost:3306/new_schema'
db = SQLAlchemy(app)
app.config['SQLALCHEMY_DATABASE_URI'] = con

MAX_CONTEXT = 10


class SearchForm(Form):
    """ search form """
    search_term = StringField('Search corpus')
    data_choice = RadioField('Label', choices=[('concordance', 'Concordance'),
                             ('word_data', 'Word data')])


class LexiconTable(db.Model):
    """ creates the lexicon table and matches the schema """
    word = db.Column(db.String(100), unique=True)
    hash_id = db.Column(db.Integer(), primary_key=True)

    def __init__(self, word, hash_id):
        self.word = word
        self.id = hash_id

    def __repr__(self):
        return f'<LexiconTable {self.word}, {self.hash_id}>'


class WsepTable(db.Model):
    """ creates the wichí spanish english parse table """
    wichi = db.Column(db.String(100), primary_key=True)
    spanish = db.Column(db.String(100))
    english = db.Column(db.String(100))
    part_of_speech = db.Column(db.String(100))
    source = db.Column(db.String(100))
    parse = db.Column(db.String(100))

    def __init__(self, wichi, spanish, english,
                 part_of_speech, source, parse):
        self.wichi = wichi
        self.spanish = spanish
        self.english = english
        self.part_of_speech = part_of_speech
        self.source = source
        self.parse = parse

    def __repr__(self):
        return (f'<WsepTable `wichi`: {wichi}, `spanish`: {spanish}, '
                f'`english`: {english}, `part_of_speech`: {part_of_speech}, '
                f'`source`: {source}, `parse`: {parse}>')


class CorpusTable(db.Model):
    """ creates the lexicon table and matches the schema
        `text_posi` is the primary_key. """
    text_posi = db.Column(db.Integer(), primary_key=True)
    text_id = db.Column(db.Integer())
    text_nme = db.Column(db.String(100))
    word_id = db.Column(db.Integer())

    def __init__(self, text_posi, text_id, text_nme, word_id):
        self.text_posi = text_posi
        self.text_id = text_id
        self.text_nme = text_nme
        self.word_id = word_id

    def __repr__(self):
        return_string = (f'<CorpusTable {self.text_posi} '
                         f'{self.text_id} '
                         f'{self.text_nme} '
                         f'{self.word_id}>')
        return return_string


# ct = CorpusTable.query.all()
# lt = LexiconTable.query.all()


def n_context(pos_id, n):
    """ returns list of `n` tokens in either
        direction of a given `pos_id`

        e.g. n-tokens in either direction of the given pos_id
        n = 2
        232 233 [234] 235 236
         2   1    -    1   2
        This function does _not_ handle for out-of-index pos_ids
    """
    # make sure that number isn't negative
    n = abs(n)
    # n is reset if larger than max_context
    if n >= MAX_CONTEXT:
        n = MAX_CONTEXT

    context = [i for i in range(pos_id - n, pos_id + n)
               if i > 0 and i <= 131199]

    return context

# class search_result():

# corpus_table = CorpusTable.query.all()
# lexicon_table = LexiconTable.query.all()


class SearchResult:
    """ class to store results in """
    pass


# def word_data_search(term):
#     """ goes and gets data from the wsep table """
#     try:


def search(term, choice, context_amt):
    """ change term to id, get context, return corpus table result object """
    b = SearchResult()

    if choice == 'word_data':
        b.word_data = True
        b.concordance = False
        print(choice, b.word_data)
    if choice == 'concordance':
        b.concordance = True
        b.word_data = False
        print(choice, b.concordance)
    if choice == 'None':
        b.display = False
        b.word_data = False
        b.concordance = False

    try:
        word_info = LexiconTable.query.filter_by(word=term).first()
        hashed = word_info.hash_id
        corpus_query = CorpusTable.query.filter_by(word_id=hashed).all()
        word_freq = len(corpus_query)
        b.term = term
    except AttributeError:
        b.display = False
        return b

    if b.word_data:
        # display data
        # try:
        Res = WsepTable.query.filter_by(wichi=term).first()
        try:
            b.type = 'word_data'
            b.word_freq = word_freq
            b.wichi = Res.wichi
            b.spanish = Res.spanish
            b.english = Res.english
            b.part_of_speech = Res.part_of_speech
            b.source = Res.source
            b.parse = Res.parse
        except AttributeError:
            b.word_data = False
            return b

    elif b.concordance:
        # try:
        b.phrases = []
        b.text_nmes = []
        loops = 0

        for Item in corpus_query:
            # r_dict['context'] = n_context(r_dict['text_posi'], context_amt)
            context = n_context(Item.text_posi, context_amt)
            words = []
            # print('len of result.context', len(Result.context))
            for number in context:
                # filter the corpus table on the context of the word
                Qobj = CorpusTable.query.filter_by(text_posi=number).first()
                # filter the lexicon table to get the word
                Word = LexiconTable.query.filter_by(hash_id=Qobj.word_id).first()
                words.append(Word.word)
                phrase = ' '.join(words)
            # Result.word_list = words
            # Item.word_list = words
            b.type = 'concordance'
            b.phrases.append(phrase)
            b.word_freq = word_freq
            b.text_nmes.append(Item.text_nme)

            loops += 1
            if loops == 100:
                break
            # except AttributeError:
            #     print('attribute error')
            # return res_objs

            b.ph_txt = list(zip(b.phrases, b.text_nmes))

    # except AttributeError:
        # b.no_error = False
        # return b
    b.display = True
    return b


@app.route('/', methods=['GET', 'POST'])
def index():
    form = SearchForm(request.form)
    print('form.data', form.data)
    term_from_html = form.data['search_term']
    choice = form.data['data_choice']
    res_obj = search(term_from_html, choice, 5)

    if request.method == 'POST' and form.data['search_term'] != '':
        res_obj.display = True
    return render_template('index.html',
                           form=form,
                           res_obj=res_obj)

if __name__ == '__main__':
    app.run()  # remove this before deployment
    # debug=True
