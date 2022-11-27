from chatterbot.trainers import ListTrainer


def treinar_bot(chatbot, lista_frases, reiniciar=False):
    if reiniciar:
        chatbot.storage.drop()
    trainer = ListTrainer(chatbot)
    trainer.train(lista_frases)


def buscar_conversas(app, modelConversa):
    with app.app_context():
        conversas = modelConversa.query.all()
        conversas = [conversa.to_json() for conversa in conversas]

        lista_conversas = []
        for conversa in conversas:
            lista_conversas.append(conversa['pergunta'])
            lista_conversas.append(conversa['resposta'])
        
        return lista_conversas
