import mysql.connector
from mysql.connector import Error
from ruxit.api.base_plugin import RemoteBasePlugin
import logging

logger = logging.getLogger(__name__)

class NotificacaoInfracaoAtraso(RemoteBasePlugin):

    def query(self, **kwargs):

        global con, resultado_notificacao_infracao

        resultado_notificacao_infracao = "OK"
        statusOK = "OK"
        statusNOTOK = "Bad"

        try:
            con = mysql.connector.connect(host='ct-rds-prd-account-dispute.cluster-ceip7fi02lcw.sa-east-1.rds.amazonaws.com',
                                          database='dispute', user='monitoracao', password='Monit#24x7#Dyna#2022')
            consulta_sql = "SELECT ir.DICT_CREATION_DATE,\
                                   TIMESTAMPADD(DAY, 7, ir.DICT_CREATION_DATE) AS PRAZO,\
                                   TIMESTAMPDIFF(HOUR, TIMESTAMPADD(DAY, 7, ir.DICT_CREATION_DATE), NOW()) AS ATRASO_EM_HORAS\
                            FROM   DIS_INFRACTION_REPORT ir\
                            WHERE  ir.ID_STATUS IN (3, 8)\
                              AND  ir.STAKEHOLDER = 'RECEIVER'\
                              AND  ir.CREATION_DATE > TIMESTAMPADD(DAY, -30, NOW())\
                              AND  TIMESTAMPADD(DAY, 6, ir.DICT_CREATION_DATE) < NOW()\
                            ORDER BY TIMESTAMPDIFF(HOUR, TIMESTAMPADD(DAY, 7, ir.DICT_CREATION_DATE), NOW()) DESC;"

            cursor = con.cursor()
            cursor.execute(consulta_sql)
            count_linhas = len(cursor.fetchall())

            total_linhas_atraso_notificacao_infracao = count_linhas

            if total_linhas_atraso_notificacao_infracao == 0:
                resultado_notificacao_infracao = statusOK
                print("Status:", resultado_notificacao_infracao)
            else:
                resultado_notificacao_infracao = statusNOTOK
                print("Status:", resultado_notificacao_infracao)

            group = self.topology_builder.create_group("ANS DICT - Atrasos", "ANS DICT - Atrasos")
            device = group.create_element("Notificação Infração", "Notificação Infração")
            group.report_property(key="Desenvolvedor", value="Rodrigo Biaggio")
            group.report_property(key="Secondary technology", value="MySQL")
            group.report_property(key="Integrações", value="AWS")
            group.report_property(key="Descrição", value="Diretório de Identificadores de Contas Transacionais")
            device.report_property(key="Database Name", value="addressing")
            device.report_property(key="Integrações", value="AWS")
            device.report_property(key="Technology", value="Python")
            device.report_property(key="Secondary technology", value="MySQL")
            device.add_endpoint(ip="10.28.50.53", port=3306,
                                dnsNames=["mip-prd-cluster-addressing-2.ceip7fi02lcw.sa-east-1.rds.amazonaws.com"])
            device.relative(key='total_linhas_atraso_notificacao_infracao',
                            value=total_linhas_atraso_notificacao_infracao)
            group.absolute(key='total_linhas_atraso_notificacao_infracao',
                           value=total_linhas_atraso_notificacao_infracao)
            device.state_metric(key='resultado_notificacao_infracao', value=resultado_notificacao_infracao)
            print("Notificação Infração Atraso: ", total_linhas_atraso_notificacao_infracao)

        except Error as e:
            print("Erro ao acessar tabela", e)

        finally:
            print("Conexão ao banco encerrada")