import mysql.connector
from mysql.connector import Error
from ruxit.api.base_plugin import RemoteBasePlugin
import logging

logger = logging.getLogger(__name__)


class ConfirmarReivindicacaoAtraso(RemoteBasePlugin):

    def query(self, **kwargs):

        global con, resultado_confirmar_reivindicacao

        resultado_confirmar_reivindicacao = "OK"
        statusOK = "OK"
        statusNOTOK = "Bad"

        try:
            con = mysql.connector.connect(host='mip-prd-cluster-addressing-2.ceip7fi02lcw.sa-east-1.rds.amazonaws.com',
                                          database='addressing', user='9001088', password='9001088#2022#')
            consulta_sql = "SELECT claim.RESOLUTION_PERIOD_END,\
                                   claim.LOCAL_CREATION_DATE,\
                                   claim.STATUS,\
                                   claim.LOCAL_LAST_MODIFIED,\
                                   claim.LAST_MODIFIED,\
                                   TIMESTAMPDIFF(MINUTE, RESOLUTION_PERIOD_END, NOW()) MINUTOS\
                            FROM   AD_CLAIM claim\
                            WHERE  TYPE = 'OWNERSHIP'\
                              AND  STAKEHOLDER = 'DONOR'\
                              AND  STATUS IN ('PENDING_USER_CONFIRMATION', 'RECEIVED')\
                              AND  OPERATION_REASON = 'DEFAULT_OPERATION'\
                              AND  TIMESTAMPDIFF(MINUTE, RESOLUTION_PERIOD_END, NOW()) > 60\
                            ORDER BY TIMESTAMPDIFF(MINUTE, RESOLUTION_PERIOD_END, NOW()) DESC;"

            cursor = con.cursor()
            cursor.execute(consulta_sql)
            count_linhas = len(cursor.fetchall())

            total_linhas_atraso_confirmar_reivindicacao = count_linhas

            if total_linhas_atraso_confirmar_reivindicacao == 0:
                resultado_confirmar_reivindicacao = statusOK
                print("Status:", resultado_confirmar_reivindicacao)
            else:
                resultado_confirmar_reivindicacao = statusNOTOK
                print("Status:", resultado_confirmar_reivindicacao)

            group = self.topology_builder.create_group("ANS DICT - Atrasos", "ANS DICT - Atrasos")
            device = group.create_element("Confirmar Reivindicação", "Confirmar Reivindicação")
            group.report_property(key="Desenvolvedor", value="Rodrigo Biaggio")
            group.report_property(key="Secondary technology", value="MySQL")
            group.report_property(key="Integrações", value="AWS")
            group.report_property(key="Descrição", value="Diretório de Identificadores de Contas Transacionais")
            device.report_property(key="Database Name", value="addressing")
            device.report_property(key="Integrações", value="AWS")
            device.report_property(key="Technology", value="Python")
            device.report_property(key="Secondary technology", value="MySQL")
            device.add_endpoint(ip="10.28.50.53", port=3306, dnsNames=["mip-prd-cluster-addressing-2.ceip7fi02lcw.sa-east-1.rds.amazonaws.com"])
            device.relative(key='total_linhas_atraso_confirmar_reivindicacao',
                            value=total_linhas_atraso_confirmar_reivindicacao)
            group.absolute(key='total_linhas_atraso_confirmar_reivindicacao',
                           value=total_linhas_atraso_confirmar_reivindicacao)
            device.state_metric(key='resultado_confirmar_reivindicacao', value=resultado_confirmar_reivindicacao)
            print("Confirmações Reivindicação Atraso: ", total_linhas_atraso_confirmar_reivindicacao)

        except Error as e:
            print("Erro ao acessar tabela", e)

        finally:
            cur = con.cursor()
        if con.is_connected():
            con.close()
            cur.close()
            print("Conexão ao banco encerrada")