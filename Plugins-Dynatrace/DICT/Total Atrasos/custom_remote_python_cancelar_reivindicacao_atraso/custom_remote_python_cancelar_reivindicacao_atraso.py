import mysql.connector
from mysql.connector import Error
from ruxit.api.base_plugin import RemoteBasePlugin
import logging

logger = logging.getLogger(__name__)


class CancelarReivindicacaoAtraso(RemoteBasePlugin):

    def query(self, **kwargs):

        global con, resultado_cancelar_reivindicacao

        resultado_cancelar_reivindicacao = "OK"
        statusOK = "OK"
        statusNOTOK = "Bad"

        try:
            con = mysql.connector.connect(host='mip-prd-cluster-addressing-2.ceip7fi02lcw.sa-east-1.rds.amazonaws.com',
                                          database='addressing', user='9001088', password='9001088#2022#')
            consulta_sql = "SELECT TIMESTAMPADD(DAY, 30, claim.LOCAL_CREATION_DATE) FINAL_PERIODO,\
                                   TIMESTAMPDIFF(MINUTE, TIMESTAMPADD(DAY, 30, claim.LOCAL_CREATION_DATE), NOW()) MINUTOS,\
                                   claim.LOCAL_CREATION_DATE,\
                                   claim.STATUS,\
                                   claim.LOCAL_LAST_MODIFIED,\
                                   claim.LAST_MODIFIED\
                            FROM   AD_CLAIM claim\
                            WHERE  TYPE = 'OWNERSHIP'\
                              AND  STAKEHOLDER = 'CLAIMER'\
                              AND  STATUS = 'CONFIRMED'\
                              AND  claim.LOCAL_CREATION_DATE < TIMESTAMPADD(MINUTE, -60, TIMESTAMPADD(DAY, -30, NOW()))"

            cursor = con.cursor()
            cursor.execute(consulta_sql)
            count_linhas = len(cursor.fetchall())

            total_linhas_atraso_cancelar_reivindicacao = count_linhas

            if total_linhas_atraso_cancelar_reivindicacao == 0:
                resultado_cancelar_reivindicacao = statusOK
                print("Status:", resultado_cancelar_reivindicacao)
            else:
                resultado_cancelar_reivindicacao = statusNOTOK
                print("Status:", resultado_cancelar_reivindicacao)

            group = self.topology_builder.create_group("ANS DICT - Atrasos", "ANS DICT - Atrasos")
            device = group.create_element("Cancelar Reivindicação", "Cancelar Reivindicação")
            group.report_property(key="Desenvolvedor", value="Rodrigo Biaggio")
            group.report_property(key="Secondary technology", value="MySQL")
            group.report_property(key="Integrações", value="AWS")
            group.report_property(key="Descrição", value="Diretório de Identificadores de Contas Transacionais")
            device.report_property(key="Database Name", value="addressing")
            device.report_property(key="Integrações", value="AWS")
            device.report_property(key="Technology", value="Python")
            device.report_property(key="Secondary technology", value="MySQL")
            device.add_endpoint(ip="10.28.50.53", port=3306, dnsNames=["mip-prd-cluster-addressing-2.ceip7fi02lcw.sa-east-1.rds.amazonaws.com"])
            device.relative(key='total_linhas_atraso_cancelar_reivindicacao',
                            value=total_linhas_atraso_cancelar_reivindicacao)
            group.absolute(key='total_linhas_atraso_cancelar_reivindicacao',
                           value=total_linhas_atraso_cancelar_reivindicacao)
            device.state_metric(key='resultado_cancelar_reivindicacao', value=resultado_cancelar_reivindicacao)
            print("Cancelamentos Reivindicação Atraso: ", total_linhas_atraso_cancelar_reivindicacao)

        except Error as e:
            print("Erro ao acessar tabela", e)

        finally:
            cur = con.cursor()
        if con.is_connected():
            con.close()
            cur.close()
            print("Conexão ao banco encerrada")