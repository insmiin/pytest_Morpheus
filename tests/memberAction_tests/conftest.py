
import pytest
from mysql.connector import Error
import mysql.connector
import requests
#import test_scenarios.myConstants as const
import tests.myConstants as const
import sys
import os
from tests.memberAction_tests.helpers.myHelperFunc import call_api
#from test_scenarios.myHelperFunc import call_api
#to add root directory into the sys.path, so that the script able to import module in root directory
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, root_dir)
from mappingModule import SportGroupMapper


@pytest.fixture(scope="session")
def mysql_connection():
    print('mysql_connection fixtureee')
    conn = None
    try:
        conn = mysql.connector.connect(
            host='35.229.171.142',
            user='sfqat_superadmin_qa',  #'qat_readonly',
            password='dL72QF1Ia4',   #'NTZ6Wt3tzqCp4k7v',
            port=3306,
            database='GB_Qat'  # !!this is DATABASEname(GB_Qat) in mysql , not the connectionName on mysql workbench....
        )
        yield conn
    except Error as err:
        pytest.fail(f"MySQL connection error: {err}")
    finally:
        print('mysql at finally')
        if conn and conn.is_connected():
            print('going to close the mysql connection')
            conn.close()


@pytest.fixture(scope="function")
def mysql_connection2():
    print('mysql_connection2222 fixtureee')
    conn = None
    try:
        conn = mysql.connector.connect(
            host='35.229.171.142',
            user='sfqat_superadmin_qa',  #'qat_readonly',
            password='dL72QF1Ia4',   #'NTZ6Wt3tzqCp4k7v',
            port=3306,
            database='GB_Qat'  # !!this is DATABASEname(GB_Qat) in mysql , not the connectionName on mysql workbench....
        )
        yield conn
    except Error as err:
        pytest.fail(f"MySQL connection22 error: {err}")
    finally:
        print('mysql2 at finally')
        if conn and conn.is_connected():
            print('going to close the mysql2 connection')
            conn.close()

@pytest.fixture(scope="session")
def api_session():
    print('api_session GB fixtureeeeee')
    session = requests.Session()
    session.headers.update(
        {"Authorization": const.AUTH_TOKEN, "Content-Type": "application/json", "Connection": "keep-alive"})
    yield session
    session.close()

@pytest.fixture(scope="session")
def api_session_SF():
    print('api_session SF fixtureeeeee')
    session = requests.Session()
    session.headers.update(
        {"Authorization": const.AUTH_TOKEN, "Content-Type": "application/json", "Connection": "keep-alive"})
    yield session
    session.close()

# Fixture to fetch companies once per session
@pytest.fixture(scope="session")
def companies_list(api_session):
    print('companies_list fixtureeeeee')
    url = f"{const.API_BASE_URL}/common/getCompanyList"
    response = call_api(api_session,'get_companies_list', 'get', url)
    assert response.status_code == 200, f"calling to 'companies_list' return {response.status_code} "
    #convert to dictionary where key is companyid and value is companyName
    return {item['companyID']: item['companyName'] for item in response.json()['data'] }


@pytest.fixture(scope="session")
def api_MemHierarchyGroupList(api_session):
    print('api_MemHierarchyGroupList fixtureeeeee')
    url = f"{const.API_BASE_URL}/MemberSetting/GetMemberCategoryGroupList"
    data = {"memberCategoryGroupName":"","companyIDs":[],"status":1,"page":1,"pageSize":10}
    response = call_api(api_session,'api_MemHierarchyGroupList', 'post', url, data)
    assert response.status_code == 200, f"calling to api_MemHierarchyGroupList return {response.status_code} "

    #extract only groupId & companies and convert into dictionary
    #eg. dict_lookup = {'IMDemo': 8, 'MINICOMMONWALLET2': 8, 'MINITRANSFERWALLET2': 8, 'MINITRANSFERWALLET3': 8}
    dict_lookup = {}
    for memCatHierGroup in response.json()['data']:
        if memCatHierGroup['status'] == 1:
            companies = [comp.strip() for comp in memCatHierGroup['companyName'].split(',')]
            for company in companies:
                dict_lookup[company] = memCatHierGroup['memberCategoryGroupID']
    return dict_lookup

# get list of finalCreditScore and its criterias
    # Mapping table for raw string operators to native Python operators
OPERATORS = {
        ">=": lambda given_value, defined_value: given_value >= defined_value,
        "<=": lambda given_value, defined_value: given_value <= defined_value,
        ">": lambda given_value, defined_value: given_value > defined_value,
        "<": lambda given_value, defined_value: given_value < defined_value,
        "==": lambda given_value, defined_value: given_value == defined_value,
    }
def get_criteria_checking_function(criteria):
    """Compiles a rule into a native, fast-executing python closure."""
    if not criteria:
        return lambda inp_value: True  #if this metric doesnt exists, means not applicable ,means no check, regardless wat value jz let it passed

    criteria_minValue, minOp = criteria.get("value"), criteria.get("valueOperator")
    criteria_maxValue, maxOp = criteria.get("value2"), criteria.get("value2Operator")

    func1 = OPERATORS[minOp] if (minOp and criteria_minValue is not None) else None #eg.func1 = lambda given_value, defined_value: given_value >= defined_value
    func2 = OPERATORS[maxOp] if (maxOp and criteria_maxValue is not None) else None
    criteria_minValue_f = float(criteria_minValue) if criteria_minValue is not None else None
    criteria_maxValue_f = float(criteria_maxValue) if criteria_maxValue is not None else None

    if func1 and func2:
        return lambda input_value: func1(input_value, criteria_minValue_f) and func2(input_value, criteria_maxValue_f)
    elif func1:
        return lambda input_value: func1(input_value, criteria_minValue_f)
    elif func2:
        return lambda input_value: func2(input_value, criteria_maxValue_f)
    return lambda input_value: True   #if any value or operator is null , means not applicable ,means no check, regardless wat value jz let it passed

@pytest.fixture(scope="session")
def api_CalcBL_CSfinalBL_mapping(api_session):
    print('api_CalcBL_CSfinalBL_mapping fixtureeeeee')
    url = f"{const.API_BASE_URL}/systemsetting/GetCreditScoreSettingListByKey"   #@@change all related....
    data = {"key": "Final_Bet_Limit_Mapping"}
    response = call_api(api_session,'api_CalcBL_CSfinalBL_mapping', 'post', url, data)
    assert response.status_code == 200, f"calling to api_CalcBL_CSfinalBL_mapping return {response.status_code} "

    CSfinalBL_calculatedBL_mapping = []
    for item in response.json()["data"]:
        # for each CS_finalBL row, put all metrics/criteria into a list
        # {  'minwager':{..,'key':'minwager','value': '0.10', 'valueOperator': '>='},'minExp':{..,'key':'minExp','value': '0.30', 'valueOperator': '>='}  }
        #criteria_dict = {s["key"]: s for s in item["settingList"]}

        # then for each metric , convert the value/operator & value2/operator2 into a lambda function
        # lastly, append {finalBL_creditScore & its criteria lambda function} into mapping dictionary
        CSfinalBL_calculatedBL_mapping.append(
            {
                "CS_finalBL_ID": item["resultValue"],  #resultValue is the betlimit valudID eg. valueID5 = 10%group
                #"func_within_defined_CalcBL_range": get_criteria_checking_function(criteria_dict.get("MinExpRatio")
                "func_within_defined_CalcBL_range": get_criteria_checking_function(item)
            }
        )
    #print(f'COMPILED_BANDSx:{CSfinalBL_calculatedBL_mapping}')
    # CSfinalBL_calculatedBL_mapping =
    # [{'CS_finalBL_ID': 1, 'func_within_defined_CalcBL_range': return lambda input >= minValue, 'check_max_avg_condition': return lambdainput >= minValue},
    #  {'CS_finalBL_ID': 2, 'func_within_defined_CalcBL_range': return lambda input >= minValue and input <=maxValue, 'check_max_avg_condition': return lambda input >= minValue},
    #  {'CS_finalBL_ID': 3, 'func_within_defined_CalcBL_range': return lambda input >= minValue, 'check_max_avg_condition': return lambda input >= minValue},
    #  ...]
    # just loop thru CSfinalBL_calculatedBL_mapping and
    # return 1st CSfinalBL_calculatedBL_mapping['CS_finalBL] if CSfinalBL_calculatedBL_mapping[CalcBL_range_condition](calculated_BL)
    # print(CSfinalBL_calculatedBL_mapping)
    # import inspect
    # func = CSfinalBL_calculatedBL_mapping[1]['func_within_defined_CalcBL_range']
    # print(inspect.getsource(func))
    return CSfinalBL_calculatedBL_mapping


# @pytest.fixture(scope="session")
# def mspID_by_rankNum():
#     ranking_lookup_mps = {v['ranking']: k for k,v in MemberProfileSettingMappers.member_profileSetting_dict.items()}
#     return ranking_lookup_mps   #{mspranking1:mspid1,mspranking2:mspid2,mspranking3:mspid3}

# @pytest.fixture(scope="session")
# def spreadID_by_rankNum():
#     ranking_lookup_spread = {v['ranking']: k for k,v in SpreadGroupMappers.member_spread_group_dict.items()}
#     return ranking_lookup_spread

# @pytest.fixture(scope="session")
# def sports_by_GbRuleID():
#     id_lookup_sport = {v['id']:v['sport']  for k,v in GbRuleMapper._mapping.items()}
#     return id_lookup_sport
#
# @pytest.fixture(scope="session")
# def sports_by_GbFeatureID():
#     id_lookup_sport = {v['id']:v['sport']  for k,v in GbFeatureMapper._mapping.items()}
#     return id_lookup_sport

@pytest.fixture(scope="session")
def prev_memberCode():
    return {"value": None}

@pytest.fixture(scope="session")
def sportGroup_sportIDs_UImap_dict(mysql_connection):
    try:
        mycursor = mysql_connection.cursor(dictionary=True)
        mysql_query = "SELECT sportID FROM GB_Qat.sports where sportID !=0"
        mycursor.execute(mysql_query)
        data = mycursor.fetchall()   #[{'sportID': 1}, {'sportID': 2}, {'sportID': 3}]
        mysql_connection.commit()  # Ends the transaction
        all_sportIDs_dict = [sport['sportID'] for sport in data]  #[1, 2, 3, 4,....,67]
    except Error as err:
        pytest.fail(f"MySQL getMemHitHistory_Mysql query error: {err}")
    finally:
        if mycursor:
            mycursor.close()

    SportGroup_SportID_mapping = SportGroupMapper.get_all()
    # Step 1: Collect all IDs that already appear in mapping (excluding key 1000)
    used_sportids = set()
    for key, value_list in SportGroup_SportID_mapping.items():
        if key != 1000:  # Skip the placeholder key 1000
            used_sportids.update(value_list)

    # Step 2: Find missing IDs (those in 'id' but not in existing_ids)
    other_sportids = [num for num in all_sportIDs_dict if num not in used_sportids]

    # Step 3: Update mapping for key 1000
    SportGroup_SportID_mapping[1000] = other_sportids
    return SportGroup_SportID_mapping  #{1001: [1], 1002: [2], 1003: [54, 55], 1000: [3, 4, 5, 6, 7, 8,etc..]}


# def test_debug(api_CalcBL_CSfinalBL_mapping):
#     print(x)