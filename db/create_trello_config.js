use prox_suporte
var dt = new Date();
var dtISO =dt.toISOString();

db.trello_config.remove()

db.trello_config.insertOne({
    'version': '1.0',
    'created_at' : ISODate("2021-12-15T16:00:00.378Z"),
    'updated_at' : ISODate("2021-12-15T16:00:00.378Z"),
    'description' : 'tabela para preenchimento do trello e aplicativo suporte do Prox',
    'types': [
        {'name': 'correcoes', 'label': 'Correções'},
        {'name': 'melhorias', 'label': 'Melhorias'}
    ],
    'status': [
        {'name': 'executando', 'label': 'Executando', 'comment': 'A solicitação está sendo executada.'},
        {'name': 'pausado', 'label': 'Pausado', 'comment': 'A solicitação foi pausada.'},
        {'name': 'cancelado', 'label': 'Cancelado', 'comment': 'A solicitação foi cancelada.'},
        {'name': 'finalizado', 'label': 'Finalizado', 'comment': 'A solicitação foi finalizada'}
    ],
    'phases': {
        'correcoes': [
            {'name': 'enviado', 'label': 'Enviado', 'comment': 'A solicitação foi enviada'},
            {'name': 'recebido', 'label': 'Recebido', 'comment': 'A solicitação foi recebida.'},
            {'name': 'solucionando', 'label': 'Solucionando', 'comment': 'A solicitação está sendo processada'},
            {'name': 'homologacao', 'label': 'Em Homologação', 'comment': 'A solicitação está em fase de homologação'},
            {'name': 'aprovado', 'label': 'Aprovada', 'comment': 'A solicitação foi aprovada'},
            {'name': 'finalizado', 'label': 'Finalizada', 'comment': 'A solicitação foi finalizada'}
        ],
        'melhorias': [
            {'name': 'enviado', 'label': 'Enviado', 'comment': 'A solicitação foi enviada'},
            {'name': 'recebido', 'label': 'Recebido', 'comment': 'A solicitação foi recebida.'},
            {'name': 'requisitos', 'label': 'Analisando Requisitos', 'comment': 'A solicitação está sendo analisanda.'},
            {'name': 'prototipando', 'label': 'Prototipando', 'comment': 'A solicitação está em fase de prototipação.'},
            {'name': 'implementando', 'label': 'Implementando', 'comment': 'A solicitação está sendo implementanda.'},
            {'name': 'teste', 'label': 'Em Teste', 'comment': 'A solicitação está em sendo testada.'},
            {'name': 'homologacao', 'label': 'Em Homologação', 'comment': 'A solicitação está em fase de homologação.'},
            {'name': 'producao', 'label': 'Em Produção', 'comment': 'A solicitação está em fase de produção.'}
        ]
    },
    'trello': {
        'correcoes': [
            {'lista': 'Correções', 'order': 0, 'phase': 'enviado', 'message': 'A solicitação foi recebida.'},
            {'lista': 'Fazer', 'order': 1, 'phase': 'recebido', 'message': 'A solicitação foi recebida.'},
            {'lista': 'Fazendo', 'order': 2, 'phase': 'solucionando', 'message': 'A solicitação está sendo processada.'},
            {'lista': 'Em homologação', 'order': 3, 'phase': 'homologacao', 'message': 'A solicitação está na fase de homologação.'},
            {'lista': 'Aprovados', 'order': 4, 'phase': 'aprovado', 'message': 'A solicitação foi aprovada.'},
            {'lista': 'Finalizados', 'order': 5, 'phase': 'finalizado', 'message': 'A solicitação foi finalizada.'}
        ],
        'melhorias':[
            {'lista': 'Melhorias', 'order': 0, 'phase': 'enviado', 'message': 'A solicitação foi recebida.'},
            {'lista': 'Fazer', 'order': 1, 'phase': 'recebido', 'message': 'A solicitação foi recebida.'},
            {'lista': 'Fazendo', 'order': 2, 'phase': 'requisitos', 'message': 'A solicitação está sendo processada.'},
            {'lista': 'Aprovado', 'order': 3, 'phase': 'resolvido', 'message': 'A solicitação foi resolvida.'},
            {'lista': 'Em homologação', 'order': 4, 'phase': 'homologacao', 'message': 'A solicitação está na fase de homologação.'},
            {'lista': 'Aprovado', 'order': 5, 'phase': 'producao', 'message': 'A solicitação de melhoria está em produção.'}
        ]
    },
    'checklist':{
        'Correções': {
            'name': 'Atividades',
            'checkitems': [{'name': 'Definir um prazo com o cliente (citar #cliente)', 'checked': 'false'}]
        },
        'Fazer': {
            'name': 'Atividades',
            'checkitems': [{'name': 'Analista alocado para a tarefa', 'checked': 'false'}]
        },
        'Fazendo': {
            'name': 'Atividades',
            'checkitems': [
                {'name': 'Problema diagnosticado', 'checked': 'false'},
                {'name': 'Solução implementada.', 'checked': 'false'}
            ]
        },
        'Em homologação': {
            'name': 'Atividades',
            'checkitems': [
                {'name': 'Testes realizados', 'checked': 'false'},
                {'name': 'Solicitar aprovação do cliente', 'checked': 'false'}
            ]
        },
        'Aprovados': {
            'name': 'Atividades',
            'checkitems': [
                {'name': 'Solicitação foi implantantada no ambiente de produção', 'checked': 'false'}
            ]
        }
    },
    'automatic_posts': {
        'Definir um prazo com o cliente (citar #cliente)':{
            'message': 'O dia %s foi definido como prazo limite para que a sua solicitação de suporte seja finalizada.\n',
            'params': 'due_date'
        },
        'Analista alocado para a tarefa':{'message': 'A sua solicitação de suporte já foi alocada ao nosso time de desenvolvimento.'},
        'Problema diagnosticado': {
            'message': ' Nosso time de desenvolvimento já pôde diagnosticar a solução para a sua solicitação de suporte.\n'+
                'Já estamos trabalhando nas implementações necessárias para resolver sua solicitação.'+
                'Em breve entraremos em contato com novidades.'
        },
        'Solução implementada.': {
            'message': 'Já finalizamos as implementações necessárias para solucionar sua solicitação.\n'+
            'Neste momento, iniciaremos a fase de testes para garantir que sua solicitação foi atendida e '+
            'que o sistema não sofra impactos negativos por conta desta nova implementação.'
        },
        'Testes realizados': {'message': 'Já finalizamos a fase de testes. Em breve as novas implementações serão publicadas no ambiente de produção'},
        'Solicitar aprovação do cliente':{
            'message': 'Já finalizamos sua demanda.\n Caso esteja de acordo e a sua solicitação atendida, por favor, clique no botão "Aprovar" ao lado.'
        },
        'Solicitação foi implantantada no ambiente de produção': {
            'message': 'Sua solicitação já foi resolvida e publicada no ambiente de produção e por este motivo, esta solicitação será finalizada.\n'+
            ' Caso precise de mais alguma ajuda, por favor, não hesite em nos contatar, '+
            'basta abrir um novo cartão.',
            'action': 'finalizar'
        }
    }
});

db.trello_config.insertOne({
    "version": "1.1",
    "created_at": ISODate("2021-12-15T16:00:00.378Z"),
    "updated_at": ISODate("2021-12-15T16:00:00.378Z"),
    "description": "tabela para preenchimento do trello e aplicativo suporte do Prox",
    'types': [
        {'name': 'correcoes', 'label': 'Correções'},
        {'name': 'melhorias', 'label': 'Melhorias'}
    ],
    'status': [
        {'name': 'executando', 'label': 'Executando', 'comment': 'A solicitação está sendo executada.'},
        {'name': 'pausado', 'label': 'Pausado', 'comment': 'A solicitação foi pausada.'},
        {'name': 'cancelado', 'label': 'Cancelado', 'comment': 'A solicitação foi cancelada.'},
        {'name': 'finalizado', 'label': 'Finalizado', 'comment': 'A solicitação foi finalizada'}
    ],
    'phases': {
        'correcoes': [
            {'name': 'enviado', 'label': 'Enviado', 'comment': 'A solicitação foi enviada'},
            {'name': 'recebido', 'label': 'Recebido', 'comment': 'A solicitação foi recebida.'},
            {'name': 'solucionando', 'label': 'Solucionando', 'comment': 'A solicitação está sendo processada'},
            {'name': 'homologacao', 'label': 'Em Homologação', 'comment': 'A solicitação está em fase de homologação'},
            {'name': 'aprovado', 'label': 'Aprovada', 'comment': 'A solicitação foi aprovada'},
            {'name': 'finalizado', 'label': 'Finalizada', 'comment': 'A solicitação foi finalizada'}
        ],
        'melhorias': [
            {'name': 'enviado', 'label': 'Enviado', 'comment': 'A solicitação foi enviada'},
            {'name': 'recebido', 'label': 'Recebido', 'comment': 'A solicitação foi recebida.'},
            {'name': 'requisitos', 'label': 'Analisando Requisitos', 'comment': 'A solicitação está sendo analisanda.'},
            {'name': 'prototipando', 'label': 'Prototipando', 'comment': 'A solicitação está em fase de prototipação.'},
            {'name': 'implementando', 'label': 'Implementando', 'comment': 'A solicitação está sendo implementanda.'},
            {'name': 'teste', 'label': 'Em Teste', 'comment': 'A solicitação está em sendo testada.'},
            {'name': 'homologacao', 'label': 'Em Homologação', 'comment': 'A solicitação está em fase de homologação.'},
            {'name': 'producao', 'label': 'Em Produção', 'comment': 'A solicitação está em fase de produção.'}
        ]
    },
    'trello': {
        'correcoes': [
            {'lista': 'Correções', 'order': 0, 'phase': 'enviado', 'message': 'A solicitação foi recebida.'},
            {'lista': 'Fazer', 'order': 1, 'phase': 'recebido', 'message': 'A solicitação foi recebida.'},
            {'lista': 'Fazendo', 'order': 2, 'phase': 'solucionando', 'message': 'A solicitação está sendo processada.'},
            {'lista': 'Em homologação', 'order': 3, 'phase': 'homologacao', 'message': 'A solicitação está na fase de homologação.'},
            {'lista': 'Aprovados', 'order': 4, 'phase': 'aprovado', 'message': 'A solicitação foi aprovada.'},
            {'lista': 'Finalizados', 'order': 5, 'phase': 'finalizado', 'message': 'A solicitação foi finalizada.'}
        ],
        'melhorias':[
            {'lista': 'Melhorias', 'order': 0, 'phase': 'enviado', 'message': 'A solicitação foi recebida.'},
            {'lista': 'Fazer', 'order': 1, 'phase': 'recebido', 'message': 'A solicitação foi recebida.'},
            {'lista': 'Fazendo', 'order': 2, 'phase': 'requisitos', 'message': 'A solicitação está sendo processada.'},
            {'lista': 'Aprovado', 'order': 3, 'phase': 'resolvido', 'message': 'A solicitação foi resolvida.'},
            {'lista': 'Em homologação', 'order': 4, 'phase': 'homologacao', 'message': 'A solicitação está na fase de homologação.'},
            {'lista': 'Aprovado', 'order': 5, 'phase': 'producao', 'message': 'A solicitação de melhoria está em produção.'}
        ]
    },
    "checklist": {
        "Correções": {
            "name": "Atividades",
            "checkitems": [
                {"name": "Definir um prazo com o cliente (enviar mensagem citando #cliente)", "checked": "false"},
                {"name": "O prazo de entrega (Due date) foi ajustado com a data combinada com o cliente", "checked": "false"}
            ]
        },
        "Fazer": {
            "name": "Atividades",
            "checkitems": [{"name": "Analista alocado para a tarefa", "checked": "false"}]
        },
        "Fazendo": {
            "name": "Atividades",
            "checkitems": [
                {"name": "Problema diagnosticado", "checked": "false"},
                {"name": "Solução implementada.", "checked": "false"}
            ]
        },
        "Em homologação": {
            "name": "Atividades",
            "checkitems": [
                {"name": "Testes realizados", "checked": "false"},
                {"name": "Solicitar aprovação do cliente", "checked": "false"}
            ]
        },
        "Aprovados": {
            "name": "Atividades",
            "checkitems": [
                {"name": "Solicitação foi implantantada no ambiente de produção", "checked": "false"},
                {"name": "Finalizar a solicitação", "checked": "false"}
            ]
        }
    },
    "automatic_posts": {
        "O prazo de entrega (Due date) foi ajustado com a data combinada com o cliente": {
            "message": " O dia %s foi definido como prazo limite para que a sua solicitação de suporte seja finalizada.",
            "params": "due_date"
        },
        "Analista alocado para a tarefa": {"message": " A sua solicitação de suporte já foi alocada ao nosso time de desenvolvimento."},
        "Problema diagnosticado": {
            "message": " Nosso time de desenvolvimento já pôde diagnosticar a solução para a sua solicitação de suporte.\n "+
                        "Já estamos trabalhando nas implementações necessárias para resolver sua solicitação."+
                        " Em breve entraremos em contato com novidades."
        },
        "Solução implementada.": {
            "message": " Já finalizamos as implementações necessárias para solucionar sua solicitação.\n "+
                        "Neste momento, iniciaremos a fase de testes para garantir que sua solicitação foi atendida e "+
                        "que o sistema não sofra impactos negativos por conta desta nova implementação."
        },
        "Testes realizados": {"message": " Já finalizamos a fase de testes. Em breve as novas implementações serão publicadas no ambiente de produção"},
        "Solicitar aprovação do cliente": {
            "message": " Já finalizamos sua demanda.\n Caso esteja de acordo e a sua solicitação atendida, por favor, clique no botão \"Aprovar\"."
        },
        "Solicitação foi implantantada no ambiente de produção": {
            "message": " Sua solicitação já foi resolvida e publicada no ambiente de produção e por este motivo, esta solicitação será finalizada.\n "+
                        "Caso precise de mais alguma ajuda, por favor, não hesite em nos contatar, basta abrir um novo cartão."
        },
        "Finalizar a solicitação": {
            "message": " Esta solicitação foi finalizada.",
            "action": "finalizar"
        }
    }
})

db.trello_config.insertOne({
    "_id": ObjectId("6221f156c839154b8d966b24"),
    "version": "1.2",
    "created_at": ISODate("2022-03-04T11:00:38.265Z"),
    "updated_at": ISODate("2022-03-04T11:00:38.265Z"),
    "description": "tabela para preenchimento do trello e aplicativo suporte do Prox",
    "types": [
      {
        "name": "correcoes",
        "label": "Correções"
      },
      {
        "name": "melhorias",
        "label": "Melhorias"
      }
    ],
    "status": [
      {
        "name": "executando",
        "label": "Executando",
        "comment": "A solicitação está sendo executada."
      },
      {
        "name": "pausado",
        "label": "Pausado",
        "comment": "A solicitação foi pausada."
      },
      {
        "name": "cancelado",
        "label": "Cancelado",
        "comment": "A solicitação foi cancelada."
      },
      {
        "name": "finalizado",
        "label": "Finalizado",
        "comment": "A solicitação foi finalizada"
      }
    ],
    "phases": {
      "correcoes": [
        {
          "name": "enviado",
          "label": "Enviado",
          "comment": "A solicitação foi enviada"
        },
        {
          "name": "recebido",
          "label": "Recebido",
          "comment": "A solicitação foi recebida."
        },
        {
          "name": "solucionando",
          "label": "Solucionando",
          "comment": "A solicitação está sendo processada"
        },
        {
          "name": "homologacao",
          "label": "Em Homologação",
          "comment": "A solicitação está em fase de homologação"
        },
        {
          "name": "aprovado",
          "label": "Aprovada",
          "comment": "A solicitação foi aprovada"
        },
        {
          "name": "finalizado",
          "label": "Finalizada",
          "comment": "A solicitação foi finalizada"
        }
      ],
      "melhorias": [
        {
          "name": "enviado",
          "label": "Enviado",
          "comment": "A solicitação foi enviada"
        },
        {
          "name": "recebido",
          "label": "Recebido",
          "comment": "A solicitação foi recebida."
        },
        {
          "name": "requisitos",
          "label": "Analisando Requisitos",
          "comment": "A solicitação está sendo analisanda."
        },
        {
          "name": "prototipando",
          "label": "Prototipando",
          "comment": "A solicitação está em fase de prototipação."
        },
        {
          "name": "implementando",
          "label": "Implementando",
          "comment": "A solicitação está sendo implementanda."
        },
        {
          "name": "teste",
          "label": "Em Teste",
          "comment": "A solicitação está em sendo testada."
        },
        {
          "name": "homologacao",
          "label": "Em Homologação",
          "comment": "A solicitação está em fase de homologação."
        },
        {
          "name": "producao",
          "label": "Em Produção",
          "comment": "A solicitação está em fase de produção."
        }
      ]
    },
    "trello": {
      "correcoes": [
        {
          "lista": "Correções",
          "order": 0,
          "phase": "enviado",
          "message": "A solicitação foi recebida."
        },
        {
          "lista": "Fazer",
          "order": 1,
          "phase": "recebido",
          "message": "A solicitação foi recebida."
        },
        {
          "lista": "Fazendo",
          "order": 2,
          "phase": "solucionando",
          "message": "A solicitação está sendo processada."
        },
        {
          "lista": "Em homologação",
          "order": 3,
          "phase": "homologacao",
          "message": "A solicitação está na fase de homologação."
        },
        {
          "lista": "Aprovados",
          "order": 4,
          "phase": "aprovado",
          "message": "A solicitação foi aprovada."
        },
        {
          "lista": "Finalizados",
          "order": 5,
          "phase": "finalizado",
          "message": "A solicitação foi finalizada."
        }
      ],
      "melhorias": [
        {
          "lista": "Melhorias",
          "order": 0,
          "phase": "enviado",
          "message": "A solicitação foi recebida."
        },
        {
          "lista": "Fazer",
          "order": 1,
          "phase": "recebido",
          "message": "A solicitação foi recebida."
        },
        {
          "lista": "Fazendo",
          "order": 2,
          "phase": "requisitos",
          "message": "A solicitação está sendo processada."
        },
        {
          "lista": "Aprovado",
          "order": 3,
          "phase": "resolvido",
          "message": "A solicitação foi resolvida."
        },
        {
          "lista": "Em homologação",
          "order": 4,
          "phase": "homologacao",
          "message": "A solicitação está na fase de homologação."
        },
        {
          "lista": "Aprovado",
          "order": 5,
          "phase": "producao",
          "message": "A solicitação de melhoria está em produção."
        }
      ]
    },
    "checklist": {
      "Correções": {
        "name": "Atividades",
        "checkitems": [
          {
            "name": "Definir um prazo com o cliente (enviar mensagem citando #cliente)",
            "checked": "false"
          },
          {
            "name": "O prazo de entrega (Due date) foi ajustado com a data combinada com o cliente",
            "checked": "false"
          }
        ]
      },
      "Fazer": {
        "name": "Atividades",
        "checkitems": [
          {
            "name": "Analista alocado para a tarefa",
            "checked": "false"
          }
        ]
      },
      "Fazendo": {
        "name": "Atividades",
        "checkitems": [
          {
            "name": "Problema diagnosticado",
            "checked": "false"
          },
          {
            "name": "Solução implementada.",
            "checked": "false"
          }
        ]
      },
      "Em homologação": {
        "name": "Atividades",
        "checkitems": [
          {
            "name": "Testes realizados",
            "checked": "false"
          },
          {
            "name": "Solicitação foi implantantada no ambiente de produção",
            "checked": "false"
          }
        ]
      },
      "Aprovados": {
        "name": "Atividades",
        "checkitems": [
          {
            "name": "Finalizar a solicitação",
            "checked": "false"
          }
        ]
      }
    },
    "automatic_posts": {
      "O prazo de entrega (Due date) foi ajustado com a data combinada com o cliente": {
        "message": " O dia %s foi definido como prazo limite para que a sua solicitação de suporte seja finalizada.",
        "params": "due_date"
      },
      "Analista alocado para a tarefa": {
        "message": " A sua solicitação de suporte já foi alocada ao nosso time de desenvolvimento."
      },
      "Problema diagnosticado": {
        "message": " Nosso time de desenvolvimento já pôde diagnosticar a solução para a sua solicitação de suporte.\n Já estamos trabalhando nas implementações necessárias para resolver sua solicitação. Em breve entraremos em contato com novidades."
      },
      "Solução implementada.": {
        "message": " Já finalizamos as implementações necessárias para solucionar sua solicitação.\n Neste momento, iniciaremos a fase de testes para garantir que sua solicitação foi atendida e que o sistema não sofra impactos negativos por conta desta nova implementação."
      },
      "Testes realizados": {
        "message": " Já finalizamos a fase de testes. Em breve as novas implementações serão publicadas no ambiente de produção"
      },
      "Solicitação foi implantantada no ambiente de produção": {
        "message": " Sua solicitação já foi resolvida e publicada no ambiente de produção. \n Por favor, clique no botão \"Aprovar\", se a sua solicitação foi atendida e estiver de acordo. ",
        "trello_msg": "O cliente foi notificado sobre a publicação da solução. Aguarde a aprovação do cliente."
      },
      "Finalizar a solicitação": {
        "message": " Esta solicitação será finalizada. \nCaso precise de mais alguma ajuda, por favor, não hesite em nos contatar, basta abrir um novo cartão.",
        "action": "finalizar"
      }
    }
})

// Create a index
db.trello_config.createIndex({"version": 1}, {unique: true});