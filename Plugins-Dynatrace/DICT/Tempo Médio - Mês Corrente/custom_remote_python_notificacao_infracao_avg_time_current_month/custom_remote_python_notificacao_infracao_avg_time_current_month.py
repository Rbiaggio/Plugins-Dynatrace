import mysql.connector
from mysql.connector import Error
from ruxit.api.base_plugin import RemoteBasePlugin
import logging

logger = logging.getLogger(__name__)


# Definindo Classe
class NotificacaoInfracaoCurrentMonth(RemoteBasePlugin):

    def query(self, **kwargs):

        global avg_notificacao_infracao_mes_corrente, state_notificacao_infracao_mes_corrente, con

        state_notificacao_infracao_mes_corrente = 0.0
        status_ok = "OK"
        status_notok = "Bad"

        try:
            con = mysql.connector.connect(host='ct-rds-prd-account-dispute.cluster-ceip7fi02lcw.sa-east-1.rds.amazonaws.com',
                                          database='dispute', user='monitoracao', password='Monit#24x7#Dyna#2022')

            consulta_sql = "SELECT IFNULL(AVG(TIMESTAMPDIFF(DAY, ir.DICT_CREATION_DATE, ir.DICT_LAST_MODIFIED)),0) AS AVG_DIAS FROM DIS_INFRACTION_REPORT ir\
                            WHERE  ir.ID_STATUS = 7\
                              AND  ir.STAKEHOLDER = 'RECEIVER'\
                              AND  ir.CREATION_DATE >= STR_TO_DATE(CONCAT(DATE_FORMAT(NOW(), '%Y-%m'), '-01'), '%Y-%m-%d')"

            cursor = con.cursor()
            cursor.execute(consulta_sql)
            resultado_query = (cursor.fetchall())

            for linha in resultado_query:
                avg_notificacao_infracao_mes_corrente = (linha[0])
                print("Total Registros", avg_notificacao_infracao_mes_corrente)

            if state_notificacao_infracao_mes_corrente <= 21.0:
                state_notificacao_infracao_mes_corrente = status_ok
                print("Status:", state_notificacao_infracao_mes_corrente)
            else:
                state_notificacao_infracao_mes_corrente = status_notok
                print("Status:", state_notificacao_infracao_mes_corrente)

            group = self.topology_builder.create_group("ANS DICT - SLA Mês Corrente", "ANS DICT - SLA Mês Corrente")
            device = group.create_element("Enviar Notificacao Infracao - SLA Mês Corrente", "Enviar Notificacao Infracao - SLA Mês Corrente")
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
            device.relative(key='avg_notificacao_infracao_mes_corrente', value=avg_notificacao_infracao_mes_corrente)
            group.absolute(key='avg_notificacao_infracao_mes_corrente', value=avg_notificacao_infracao_mes_corrente)
            device.state_metric(key='state_notificacao_infracao_mes_corrente', value=state_notificacao_infracao_mes_corrente)

        except Error as e:
            print("Erro ao acessar tabela", e)

        finally:
            cur = con.cursor()
            if con.is_connected():
                con.close()
                cur.close()
                print("Conexão ao banco encerrada")
