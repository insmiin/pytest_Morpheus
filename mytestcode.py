from google.cloud.sql.connector import Connector
import sqlalchemy

connector = Connector()

def getconn():
    return connector.connect(
        "ghostbuster-dev:asia-east1:gb-qat-db-02",  # project:region:instance
        "pymysql",
        user="sfqat_superadmin_qa",
        password="@Td£0Vjw1J2$",
        db="GB_Qat",
    )

engine = sqlalchemy.create_engine("mysql+pymysql://", creator=getconn)

with engine.connect() as conn:
    result = conn.execute(sqlalchemy.text("SELECT * FROM memberextrainfos LIMIT 5"))
    for row in result:
        print(row)

connector.close()