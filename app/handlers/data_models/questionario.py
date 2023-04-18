"""
Copyright(C) Venidera Research & Development, Inc - All Rights Reserved
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
Written by Rafael Giordano Vieira <rafael@venidera.com>
"""

from schematics.models import Model
from schematics.types import IntType
from schematics.types import BaseType
from schematics.types import DictType
from schematics.types import FloatType
from schematics.types import ModelType
from schematics.types import StringType


class IndicadoresQuantitativos(Model):
    # Margem bruta
    margem_bruta = IntType(required=False, min_value=1)
    # Índice de Liquidez
    indice_liquidez = IntType(required=False, min_value=1)
    # Fluxo de caixa livre / Faturamento Bruto
    fcf_faturamento_bruto = IntType(required=False, min_value=1)
    # Patrimônio líquido
    patrimonio_liquido = IntType(required=False, min_value=1)
    # Capital social integralizado
    capital_social_integralizado = IntType(required=False, min_value=1)
    # Giro do ativo
    giro_ativo = IntType(required=False, min_value=1)
    # Endividamento
    endividamento = IntType(required=False, min_value=1)


class IndicadoresQualitativos(Model):
    # Tempo de existência
    tempo_existencia = IntType(required=False, min_value=1)
    # Cadeia societária
    cadeia_societaria = IntType(required=False, min_value=1)
    # Pendências Financeiras
    pendencias_financeiras = IntType(required=False, min_value=1)
    # Litígios
    litigios = IntType(required=False, min_value=1)
    # Excelência Operacional
    excelencia_operacional = IntType(required=False, min_value=1)
    # Qualidade técnica do time
    qualidade_tecnica_time = IntType(required=False, min_value=1)
    # Histórico de pontualidade nos pagamentos
    historico_pontualidade_pagamentos = IntType(
        required=False, min_value=1)


class IndicadoresGovernanca(Model):
    # Auditoria Externa
    auditoria_externa = IntType(required=False, min_value=1)
    # Conselho de Administração e Comitês específicos
    conselho_administracao_comites_especificos = IntType(
        required=False, min_value=1)
    # Planejamento Estratégico
    planejamento_estrategico = IntType(required=False, min_value=1)
    # Políticas formalizadas e disponíveis
    politicas_formalizadas_disponiveis = IntType(
        required=False, min_value=1)
    # Divulgação de informações
    divulgacao_informacoes = IntType(required=False, min_value=1)


class PrioridadeIndicadores(Model):
    # Prioridade dos indicadores quantitativos
    quantitativo = ModelType(
        IndicadoresQuantitativos,
        required=False)
    # Prioridade dos indicadores qualitativos
    qualitativo = ModelType(
        IndicadoresQualitativos,
        required=False)
    # Prioridade dos indicadores de governança
    governanca = ModelType(
        IndicadoresGovernanca,
        required=False)


class PonderacaoIndicadores(Model):
    # Ponderação para bloco com indicadores quantitativos
    quantitativo = FloatType(
        required=False, min_value=0.0, max_value=100.0)
    # Ponderação para bloco com indicadores qualitativos
    qualitativo = FloatType(
        required=False, min_value=0.0, max_value=100.0)
    # Ponderação para bloco com indicadores de governança
    governanca = FloatType(
        required=False, min_value=0.0, max_value=100.0)


class PonderacaoIndicadoresSegmentos(Model):
    # Ponderação para bloco de indicadores no segmento de Agentes com Ativos
    agentes_com_ativos = ModelType(
        PonderacaoIndicadores, required=False)
    # Ponderação para bloco de indicadores no segmento de Comercializadoras
    comercializadoras = ModelType(
        PonderacaoIndicadores, required=False)
    # Ponderação para bloco de indicadores no segmento de Consumidores
    consumidores = ModelType(
        PonderacaoIndicadores, required=False)


class PonderacaoBlocosIndicadores(Model):
    # Ponderação geral dos blocos de indicadores
    geral = ModelType(
        PonderacaoIndicadores,
        required=False)
    # Ponderação dos blocos de indicadores por segmento
    segmentos = ModelType(
        PonderacaoIndicadoresSegmentos,
        required=False)


class PonderacaoPerdaPrazoMaximo(Model):
    # Ponderação geral dos blocos de indicadores
    geral = DictType(BaseType, required=False, default=dict())
    # Ponderação dos blocos de indicadores por segmento
    segmentos = DictType(BaseType, required=False, default=dict())


class PonderacaoMetricas(Model):
    # Ponderação da estrutura de capital por meio do capital social
    capital_social = IntType(
        required=False, min_value=1, max_value=5)
    # Ponderação da estrutura de capital por meio do patrimonio liquido
    patrimonio_liquido = IntType(
        required=False, min_value=1, max_value=5)
    # Ponderação da estrutura de capital por meio do fluxo de caixa livre
    fluxo_caixa_livre = IntType(
        required=False, min_value=1, max_value=5)


class PonderacaoMetricasSegmentos(Model):
    # Ponderação da estrutura de capital no segmento de Agentes com Ativos
    agentes_com_ativos = ModelType(
        PonderacaoMetricas, required=False)
    # Ponderação da estrutura de capital no segmento de Comercializadoras
    comercializadoras = ModelType(
        PonderacaoMetricas, required=False)
    # Ponderação da estrutura de capital no segmento de Consumidores
    consumidores = ModelType(
        PonderacaoMetricas, required=False)


class PonderacaoEstruturaCapital(Model):
    # Ponderação geral da estrutura de capital
    geral = ModelType(
        PonderacaoMetricas, required=False)
    # Ponderaçãoda estrutura de capital por segmento
    segmentos = ModelType(
        PonderacaoMetricasSegmentos, required=False)


class SugestaoIndicadores(Model):
    # Sugestões para indicadores quantitativos
    quantitativo = StringType(required=False, default='')
    # Sugestões para indicadores qualitativos
    qualitativo = StringType(required=False, default='')
    # Sugestões para indicadores de governança
    governanca = StringType(required=False, default='')


class SugestaoGeralSegmentos(Model):
    # Sugestão para geral
    geral = StringType(required=False, default='')
    # Sugestão para segmentos
    segmentos = StringType(required=False, default='')


class Sugestoes(Model):
    # Sugestões para a ponderacao da perda e do prazo máximos
    ponderacao_perda_prazo_maximo = ModelType(
        SugestaoGeralSegmentos, required=False)
    # Sugestões para a ponderacao dos blocos de indicadores
    ponderacao_blocos_indicadores = ModelType(
        SugestaoGeralSegmentos, required=False)
    # Sugestões para a prioridade dos indicadores
    prioridade_indicadores = ModelType(
        SugestaoIndicadores, required=False)
    # Sugestões para a ponderacao da estrutura de capital
    ponderacao_estrutura_capital = ModelType(
        SugestaoGeralSegmentos, required=False)
    # Sugestão para fatores de restrição
    fatores_restricao = StringType(required=False, default='')
    # Sugestão para fatores de exclusão
    fatores_exclusao = StringType(required=False, default='')


class Questionario(Model):
    # Faturamento médio anual em milhões de reais
    faturamento_medio_anual_mm_reais = FloatType(required=False)
    # Margem EBITDA anual em milhões de reais
    margem_ebitda_anual_mm_reais = FloatType(required=False)
    # Perda máxima esperada em R$
    perda_maxima_esperada_reais = FloatType(required=False)
    # Ponderação das perdas e prazos máximos
    ponderacao_perda_prazo_maximo = ModelType(
        PonderacaoPerdaPrazoMaximo, required=False)
    # Ponderação dos blocos de indicadores (quanti, quali, gov)
    ponderacao_blocos_indicadores = ModelType(
        PonderacaoBlocosIndicadores, required=False)
    # Prioridades dos indicadores
    prioridade_indicadores = ModelType(
        PrioridadeIndicadores, required=False)
    # Ponderação da estrutura de capital
    ponderacao_estrutura_capital = ModelType(
        PonderacaoEstruturaCapital, required=False)
    # Sugestões
    sugestoes = ModelType(Sugestoes, required=False)
