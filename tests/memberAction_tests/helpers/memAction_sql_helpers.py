
import pytest
from mysql.connector import Error
import os
from tests.memberAction_tests.helpers.myHelperFunc import call_api, get_new_date_UTC, parse_updatedby
from tests.memberAction_tests.mappingModule import SpreadGroupMappers, MemberProfileSettingMappers, GbRuleMapper, GbFeatureMapper
import tests.memberAction_tests.memberAction_Constants as action_const

def call_mySQL_query(mysql_connection, csv_filter, sql_file,
                     p_params):  # to query mysql to get memDetails, \'is to escape '
    mycursor = None
    if p_params:
        params = p_params
    else:
        params = {
            'memberCode': csv_filter['memberCode'],
            'companyID': csv_filter['companyID']
        }
    try:
        try:
            #test_dir = os.path.dirname(__file__)  # in the same directory of running test script
            #test_dir = action_const.SQL_FILE_PATH
            #sql_path = os.path.join(test_dir, sql_file)
            sql_path = action_const.SQL_FILE_PATH / sql_file

            with open(sql_path, 'r') as f:
                mysql_query = f.read()
        except FileNotFoundError:
            pytest.xfail(f"SQL query file '{sql_file}' not found")

        mycursor = mysql_connection.cursor(dictionary=True)
        mycursor.execute(mysql_query, params)
        # --- FIX: Only fetch if the query returns a result set, else might throw sql error ---
        if mycursor.with_rows:
            data = mycursor.fetchall()
        else:
            data = []  # Return an empty list for UPDATE/INSERT queries
        #data = mycursor.fetchall()  # return 1 dict

        # fixture(scope=session) is use to setup mysql connection(i.e create once &share across all tests.
        # to ensure row is not read-lock, issue commit after every query
        mysql_connection.commit()  # Ends the transaction so that AfterHit_data will not reuse BeforeHit_data
        if sql_file == "getMemDetails_Mysql.sql":
            assert len(data) == 1, f"no member or more than 1 same member row was returned from mysql"
            return data[0]  # only expect 1 member detail to be return
        else:
            return data
    except Error as err:
        pytest.xfail(f"MySQL <{sql_file}> query error: {err}")
    finally:
        if mycursor:
            mycursor.close()


def call_mySQL_getHitHistory(mysql_connection, csv_filter, p_input_filter, p_NoAction_statusID,
                             whichHit):  # to query mysql to get memDetails, \'is to escape '
    mycursor = None
    params = {
        'memberCode': csv_filter['memberCode'],
        'companyID': csv_filter['companyID']
    }

    if p_input_filter:
        input_filter = p_input_filter
    else:
        input_filter = '1=1'

    if whichHit == 'AllHits':
        actionID_to_filter = p_NoAction_statusID
    else:
        actionID_to_filter = "''"

    try:
        try:
            #test_dir = os.path.dirname(__file__)  # in the same directory of running test script
            #test_dir = action_const.SQL_FILE_PATH
            #sql_path = os.path.join(test_dir, "getMemHitHistory_Mysql.sql")
            sql_path = action_const.SQL_FILE_PATH / "getMemHitHistory_Mysql.sql"
            with open(sql_path, 'r') as f:
                mysql_query = f.read()
        except FileNotFoundError:
            pytest.xfail("SQL query file getMemHitHistory_Mysql.sql not found: path/to/your/mysql_query.sql")

        mycursor = mysql_connection.cursor(dictionary=True)
        mysql_query = mysql_query.format(filter_statement=input_filter, action_disallowed=p_NoAction_statusID,
                                         actionID_to_filter=actionID_to_filter)
        mycursor.execute(mysql_query, params)
        data = mycursor.fetchall()
        mysql_connection.commit()  # Ends the transaction

        return data  # only expect 1 member detail to be return
    except Error as err:
        pytest.xfail(f"MySQL getMemHitHistory_Mysql query error: {err}")
    finally:
        if mycursor:
            mycursor.close()

def reset_member_hits(mysql_connection, csv_filter):
    # reset date to very old date to make sure it is outside validity period and will be ignored
    p_params = {
        'memberCode': csv_filter['memberCode'],
        'companyID': csv_filter['companyID'],
        'date_to_change_UTC': '2025-02-02 04:00:00'
    }
    call_mySQL_query(mysql_connection, csv_filter, 'reset_mem_GbFeatureHits_Mysql.sql', p_params)
    call_mySQL_query(mysql_connection, csv_filter, 'reset_mem_GbRuleHits_Mysql_msp.sql', p_params)
    call_mySQL_query(mysql_connection, csv_filter, 'reset_mem_GbRuleHits_Mysql_mspa.sql', p_params)
    call_mySQL_query(mysql_connection, csv_filter, 'reset_mem_BetDelay_Mysql.sql', p_params)


def modify_member_latestHit_attribute_date(mysql_connection, csv_filter):
    pairs = {}
    GbRule = False
    # convert prerequisite into json
    for line in csv_filter['EditUpdByDate'].splitlines():
        key, value = line.split(":")  # split by : into string on both side
        pairs[key] = value

    past_date_UTC = get_new_date_UTC(3, 'months')
    if (pairs['outsideValidPeriod']).lower() == 'yes':
        past_date_time_utc = str(past_date_UTC) + ' 03:00:00'
    else:
        past_date_time_utc = str(past_date_UTC) + ' 04:00:00'
    if GbRuleMapper.get_id_byCode(pairs['id_to_Upd']):
        HitType_ID = GbRuleMapper.get_id_byCode(pairs['id_to_Upd'])
        HitType_updbyName = GbRuleMapper.get_updByName_byCode(pairs['id_to_Upd'])
        GbRule = True
    else:
        HitType_ID = GbFeatureMapper.get_id_byCode(pairs['id_to_Upd'])
        HitType_updbyName = GbFeatureMapper.get_updByName_byCode(pairs['id_to_Upd'])
    p_params = {
        'memberCode': csv_filter['memberCode'],
        'companyID': csv_filter['companyID'],
        'date_to_change_UTC': past_date_time_utc,
        'use_ruleID_to_update': HitType_ID,
        'use_ruleUpdByName_to_update_BD': HitType_updbyName + '%'
        # BD use updateName, so make sure cater for prefix _1 &_2
    }
    print(f'p_params is ,{p_params}')
    if GbRule:
        call_mySQL_query(mysql_connection, csv_filter, 'edit_UpdByDate_GbRuleHits_Mysql_msp.sql', p_params)
        call_mySQL_query(mysql_connection, csv_filter, 'edit_UpdByDate_GbRuleHits_Mysql_mspa.sql', p_params)
    else:
        call_mySQL_query(mysql_connection, csv_filter, 'edit_UpdByDate_GbFeatureHits_Mysql.sql', p_params)

    call_mySQL_query(mysql_connection, csv_filter, 'edit_UpdByDate_BD_Mysql.sql', p_params)
    call_mySQL_query(mysql_connection, csv_filter, 'edit_UpdByDate_BLSGMemCat_Mysql.sql', p_params)