from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from chatterbot import ChatBot
from spacy.cli import download
from utils import bot_utils

# Configurações da aplicação --------------------------------------------------
db = SQLAlchemy()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///banco.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JSON_SORT_KEYS'] = False
app.config['JSON_AS_ASCII'] = False
app.secret_key = b'\r\xdd\x13\xe1\x0c2X.\xb7\xb5.\xd6+\x07SF'

db.init_app(app)

# Models do banco de dados ----------------------------------------------------
class Conversa(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pergunta = db.Column(db.String, nullable=False)
    resposta = db.Column(db.String, nullable=False)

    def to_json(self):
        return {'pergunta': self.pergunta, 'resposta': self.resposta}

# Cria o banco de dados
with app.app_context():
    db.create_all()

# Configurando o chatbot-------------------------------------------------------
# A linha abaixo so precisa ser executada uma vez
# download("en_core_web_sm")

class ENGSM:
    ISO_639_1 = 'en_core_web_sm'

chatbot = ChatBot("BotLibim", tagger_language=ENGSM, read_only=True)

# Reinicia o banco de dados do bot com as frases salvas no nosso banco
lista_conversas = bot_utils.buscar_conversas(app, Conversa)
bot_utils.treinar_bot(chatbot, lista_conversas, reiniciar=True)

# Rotas da aplicacao web ------------------------------------------------------
@app.route('/')
def index():
    return redirect(url_for('chat'))


@app.route('/conversa/index', methods=['GET'])
def conversa_index():
    conversas = Conversa.query.all()
    return render_template('conversa/index.html', conversas=conversas)


@app.route('/conversa/create', methods=['GET'])
def conversa_create():
    return render_template('conversa/create.html')


@app.route('/conversa/store', methods=['POST'])
def conversa_store():
    perguntas = request.form.getlist('pergunta[]')
    respostas = request.form.getlist('resposta[]')

    lista_frases = []

    for i in range(len(perguntas)):
        conversa = Conversa(pergunta=perguntas[i], resposta=respostas[i])
        db.session.add(conversa)

        lista_frases.append(perguntas[i])
        lista_frases.append(respostas[i])
    
    db.session.commit()

    # Treina o chatbot com as novas conversas salvas
    bot_utils.treinar_bot(chatbot, lista_frases)

    session['dados_criados'] = True
    return redirect(url_for('conversa_create'))


@app.route('/conversa/delete/<int:id>', methods=['GET'])
def conversa_delete(id):
    Conversa.query.filter_by(id=id).delete()
    db.session.commit()

    # Retreina o bot
    lista_conversas = bot_utils.buscar_conversas(app, Conversa)
    bot_utils.treinar_bot(chatbot, lista_conversas, reiniciar=True)

    session['dados_excluidos'] = True
    return redirect(url_for('conversa_index'))


@app.route('/chatbot')
def chat():
    return render_template('chatbot/index.html')


# Rotas da API ----------------------------------------------------------------
@app.route('/api/bot', methods=['POST'])
def bot_response():
    body = request.get_json()
    msg = body["mensagem"]
    
    resposta = chatbot.get_response(msg)
    resposta = {"resposta": str(resposta)}

    return jsonify(resposta)


app.run(debug=True)
