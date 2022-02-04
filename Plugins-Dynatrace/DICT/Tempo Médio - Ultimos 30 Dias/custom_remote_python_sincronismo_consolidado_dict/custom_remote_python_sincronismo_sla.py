import mysql.connector
from mysql.connector import Error
from ruxit.api.base_plugin import RemoteBasePlugin
import logging

logger = logging.getLogger(__name__)


# Definindo Classe
class SincronismoSLA(RemoteBasePlugin):

    def query(self, **kwargs):

        try:
            con = mysql.connector.connect(host='mip-prd-cluster-addressing-2.ceip7fi02lcw.sa-east-1.rds.amazonaws.com',
                                          database='addressing', user='9001088', password='9001088#2022#')

            consulta_sql = "SELECT MIN(TIMESTAMPDIFF(HOUR,\
                             COALESCE(previousSync.CHECK_AFTER_VSYNC_REBUILD_TIMESTAMP_UTC, COALESCE(previousSync.CHECK_AFTER_CID_FILES_ADJUSTS_TIMESTAMP_UTC, previousSync.FIRST_CHECK_TIMESTAMP_UTC)),\
                             COALESCE(sync.CHECK_AFTER_VSYNC_REBUILD_TIMESTAMP_UTC, COALESCE(sync.CHECK_AFTER_CID_FILES_ADJUSTS_TIMESTAMP_UTC, sync.FIRST_CHECK_TIMESTAMP_UTC)))) AS MIN,\
                           AVG(TIMESTAMPDIFF(HOUR, COALESCE(previousSync.CHECK_AFTER_VSYNC_REBUILD_TIMESTAMP_UTC, COALESCE(previousSync.CHECK_AFTER_CID_FILES_ADJUSTS_TIMESTAMP_UTC, previousSync.FIRST_CHECK_TIMESTAMP_UTC)),\
                             COALESCE(sync.CHECK_AFTER_VSYNC_REBUILD_TIMESTAMP_UTC, COALESCE(sync.CHECK_AFTER_CID_FILES_ADJUSTS_TIMESTAMP_UTC, sync.FIRST_CHECK_TIMESTAMP_UTC)))) AS AVG,\
                           MAX(TIMESTAMPDIFF(HOUR,COALESCE(previousSync.CHECK_AFTER_VSYNC_REBUILD_TIMESTAMP_UTC, COALESCE(previousSync.CHECK_AFTER_CID_FILES_ADJUSTS_TIMESTAMP_UTC, previousSync.FIRST_CHECK_TIMESTAMP_UTC)),\
                             COALESCE(sync.CHECK_AFTER_VSYNC_REBUILD_TIMESTAMP_UTC, COALESCE(sync.CHECK_AFTER_CID_FILES_ADJUSTS_TIMESTAMP_UTC, sync.FIRST_CHECK_TIMESTAMP_UTC)))) AS MAX FROM   AD_SYNCHRONIZATION sync,\
                           AD_SYNCHRONIZATION previousSync WHERE  sync.STATUS = 9 -- SYNCHRONIZATION_ENDED_OK AND  previousSync.STATUS = 9 AND  previousSync.KEY_TYPE = sync.KEY_TYPE\
                      AND  COALESCE(previousSync.CHECK_AFTER_VSYNC_REBUILD_TIMESTAMP_UTC, COALESCE(previousSync.CHECK_AFTER_CID_FILES_ADJUSTS_TIMESTAMP_UTC, previousSync.FIRST_CHECK_TIMESTAMP_UTC)) =\
                            (SELECT MAX(COALESCE(syncAux.CHECK_AFTER_VSYNC_REBUILD_TIMESTAMP_UTC, COALESCE(syncAux.CHECK_AFTER_CID_FILES_ADJUSTS_TIMESTAMP_UTC, syncAux.FIRST_CHECK_TIMESTAMP_UTC)))\
                             FROM   AD_SYNCHRONIZATION syncAux WHERE  syncAux.KEY_TYPE = sync.KEY_TYPE AND  syncAux.STATUS = 9 AND  (COALESCE(syncAux.CHECK_AFTER_VSYNC_REBUILD_TIMESTAMP_UTC, COALESCE(syncAux.CHECK_AFTER_CID_FILES_ADJUSTS_TIMESTAMP_UTC, syncAux.FIRST_CHECK_TIMESTAMP_UTC)))\
                                    < COALESCE(sync.CHECK_AFTER_VSYNC_REBUILD_TIMESTAMP_UTC, COALESCE(sync.CHECK_AFTER_CID_FILES_ADJUSTS_TIMESTAMP_UTC, sync.FIRST_CHECK_TIMESTAMP_UTC)))\
                      AND sync.FIRST_CHECK_TIMESTAMP_UTC > TIMESTAMPADD(DAY, -30, NOW());"

            cursor = con.cursor()
            cursor.execute(consulta_sql)
            sincronismo_registros = (cursor.fetchall())

            for linha in sincronismo_registros:
                sincronismo_consolidado = (linha[1])
                print(sincronismo_consolidado)

            group = self.topology_builder.create_group("DICT - SLA", "DICT - SLA")
            device = group.create_element("Sincronismo - SLA", "Sincronismo - SLA")
            group.report_property(key="Desenvolvedor", value="Rodrigo Biaggio")
            group.report_property(key="Integrações", value="AWS-RDS")
            group.report_property(key="Descrição", value="Diretório de Identificadores de Contas Transacionais")
            device.report_property(key="Database Name", value="addressing")
            device.report_property(key="Integrações", value="AWS-RDS")
            device.add_endpoint(ip="10.28.50.53", port=3306, dnsNames=["Pix"])
            device.relative(key='sincronismo_consolidado', value=sincronismo_consolidado)
            group.absolute(key='sincronismo_consolidado', value=sincronismo_consolidado)
            device.state_metric(key='sincronismo_consolidado', value=sincronismo_consolidado)

        except Error as e:
            print("Erro ao acessar tabela", e)

        finally:
            cur = con.cursor()
            if con.is_connected():
                con.close()
                cur.close()
                print("Conexão ao banco encerrada")
