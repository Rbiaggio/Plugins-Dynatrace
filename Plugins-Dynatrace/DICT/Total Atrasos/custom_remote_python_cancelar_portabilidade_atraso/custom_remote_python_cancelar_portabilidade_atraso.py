import mysql.connector
from mysql.connector import Error
from ruxit.api.base_plugin import RemoteBasePlugin
import logging

logger = logging.getLogger(__name__)

class CancelarPortabilidadeAtraso(RemoteBasePlugin):

    def query(self, **kwargs):

        global total_linhas_atraso, con, resultado_cancelar_portabilidade

        total_linhas_atraso = 0
        resultado_cancelar_portabilidade = "OK"
        statusOK = "OK"
        statusNOTOK = "Bad"
        jdbc: mysql: // mip-prd-cluster-addressing-2.ceip7fi02lcw.sa-east-1.rds.amazonaws.com:3306/addressing
        try:
            con = mysql.connector.connect(host='mip-prd-cluster-addressing-2.ceip7fi02lcw.sa-east-1.rds.amazonaws.com',
                                          database='addressing', user='9001088', password='')
            consulta_sql = "SELECT claim.RESOLUTION_PERIOD_END,\
                                   claim.LOCAL_CREATION_DATE,\
                                   claim.STATUS,\
                                   claim.LOCAL_LAST_MODIFIED,\
                                   claim.LAST_MODIFIED,\
                                   TIMESTAMPDIFF(MINUTE, RESOLUTION_PERIOD_END, NOW()) MINUTOS\
                            FROM   AD_CLAIM claim\
                            WHERE  TYPE = 'PORTABILITY'\
                              AND  STAKEHOLDER = 'DONOR'\
                              AND  STATUS IN ('PENDING_USER_CONFIRMATION', 'WAITING_CONFIRMATION_DISPATCH', 'RECEIVED')\
                              AND  TIMESTAMPDIFF(MINUTE, RESOLUTION_PERIOD_END, NOW()) > 60\
                            ORDER BY TIMESTAMPDIFF(MINUTE, RESOLUTION_PERIOD_END, NOW()) DESC;"

            cursor = con.cursor()
            cursor.execute(consulta_sql)
            count_linhas = len(cursor.fetchall())

            total_linhas_atraso_cancelar_portabilidade = count_linhas

            if total_linhas_atraso_cancelar_portabilidade == 0:
                resultado_cancelar_portabilidade = statusOK
                print("Status:", resultado_cancelar_portabilidade)
            else:
                resultado_cancelar_portabilidade = statusNOTOK
                print("Status:", resultado_cancelar_portabilidade)

            group = self.topology_builder.create_group("ANS DICT - Atrasos", "ANS DICT - Atrasos")
            device = group.create_element("Cancelar Portabilidade", "Cancelar Portabilidade")
            group.report_property(key="Desenvolvedor", value="Rodrigo Biaggio")
            group.report_property(key="Secondary technology", value="MySQL")
            group.report_property(key="Integrações", value="AWS")
            group.report_property(key="Descrição", value="Diretório de Identificadores de Contas Transacionais")
            device.report_property(key="Database Name", value="addressing")
            device.report_property(key="Integrações", value="AWS")
            device.report_property(key="Technology", value="Python")
            device.report_property(key="Secondary technology", value="MySQL")
            device.add_endpoint(ip="10.28.50.53", port=3306, dnsNames=["mip-prd-cluster-addressing-2.ceip7fi02lcw.sa-east-1.rds.amazonaws.com"])
            device.relative(key='total_linhas_atraso_cancelar_portabilidade',
                            value=total_linhas_atraso_cancelar_portabilidade)
            group.absolute(key='total_linhas_atraso_cancelar_portabilidade',
                           value=total_linhas_atraso_cancelar_portabilidade)
            device.state_metric(key='resultado_cancelar_portabilidade', value=resultado_cancelar_portabilidade)
            print("Cancelamentos Portabilidade Atraso: ", total_linhas_atraso_cancelar_portabilidade)

        except Error as e:
            print("Erro ao acessar tabela", e)

        finally:
            cur = con.cursor()
        if con.is_connected():
            con.close()
            cur.close()
            print("Conexão ao banco encerrada")