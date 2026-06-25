
from tests.memberAction_tests.helpers.myHelperFunc import call_api, get_new_date_UTC, parse_updatedby
from tests.utils.comparison_utils import is_match, is_LT
from tests.memberAction_tests.mappingModule import SpreadGroupMappers, MemberProfileSettingMappers, GbRuleMapper, GbFeatureMapper
import ast





def get_ranking_byID(value, type):
    if type == 'msp':
        rankNum = MemberProfileSettingMappers.get_ranking_by_ID(value)
    else:
        rankNum = SpreadGroupMappers.get_ranking_by_ID(value)
    return rankNum


def get_most_severe(rankNum, smallest_rankNum):
    if smallest_rankNum == None or is_LT(rankNum, smallest_rankNum):
        smallest_rankNum = rankNum
    return smallest_rankNum



def get_most_severe_value_from_all_moduleHits(hitObject, moduleHistory_after_hit, smallest_ranking_number_msp,
                                              smallest_ranking_number_spread, sportGroup_sportIDs_UImap_dict,
                                              betDelay_Severest_dict):
    memCategory_of_directEGON = None
    isAdvised_of_directEGON = None
    BetDelay_of_directEGON = None
    # loop thru each hits(history+current) to determine if need pick up to process or not
    for hitmodule in moduleHistory_after_hit:
        # rank1 is most severe/highest hierarchy.
        # each member can only hit either ML_UI_Level_Robot or ML_UI_Level_Arber in lifetime. do not trigger both in same member. will give unexpected result..
        # if (hitmodule['scr_gbRuleID'] == '7' and new_Hit_Action['prof_moduleID'] == '84') or (hitmodule['prof_moduleID'] == '84' and new_Hit_Action['scr_gbRuleID'] == '7'):
        #    continue

        # if GBBad & EGON good & newHit=EGON, noAction directly
        if (hitObject.cross_GB_Bad and hitObject.cross_EGON_Good and is_match(hitObject.HitID, 11)):
            break

        # if GBBad & EGON good & newHit=NonEGON, skip EGON (to use only GBrule/feature for comparison)
        # if GBGood & hasEGON,skip all non-EGON(gbrule/gbfeature) & process only EGON (EGON's BL,SG,BD straightaway become most severe since only got EGON)
        if (hitObject.cross_GB_Good and hitObject.cross_has_EGON and not is_match(hitmodule['scr_gbRuleID'], 11)) or \
                (hitObject.cross_GB_Bad and hitObject.cross_EGON_Good and is_match(hitmodule['scr_gbRuleID'], 11)):
            continue

        # skip hitModule that has memberSettingProfile/spreadGroup defined as 'NoAction'/null
        if hitmodule['UpdateMemberProfile'] is not None:  # i.e. has actionValue defined
            rankNum_msp = get_ranking_byID(hitmodule['UpdateMemberProfile'], 'msp')
            if smallest_ranking_number_msp == None or is_LT(rankNum_msp, smallest_ranking_number_msp):
                smallest_ranking_number_msp = rankNum_msp
        if hitmodule['UpdateMemberSpreadGroup'] is not None:  # has actionValue defined
            rankNum_spread = get_ranking_byID(hitmodule['UpdateMemberSpreadGroup'], 'spread')
            if smallest_ranking_number_spread == None or is_LT(rankNum_spread, smallest_ranking_number_spread):
                smallest_ranking_number_spread = rankNum_spread

        if hitmodule['UpdateMemberBetDelay'] is not None:  # i.e. has actionValue defined
            Module_BetDelay = int(hitmodule['UpdateMemberBetDelay'])
            # hitmodule['UpdateBDSportGroups'] contains SportGroup format, i.e ['1001','1003']
            # we convert it into individual sportID and store in BDsportIDs for processing, i.e [1,54,55]
            BDsportIDs = []
            thismodule_SportGroup_list = ast.literal_eval(
                hitmodule['UpdateBDSportGroups'])  # >reformat '[1001,1002]'  to [1001,1002]
            # print(f"hitmodule['UpdateBDSportGroups'] 111 is ,",thismodule_SportGroup_list)
            if thismodule_SportGroup_list == [-1]:
                for sportGroup in sportGroup_sportIDs_UImap_dict:  # get all from {1001: [1], 1002: [2], 1003: [54, 55], 1000: [3, 4, 5, 6, 7, 8,etc..]}
                    BDsportIDs.extend(sportGroup_sportIDs_UImap_dict.get(sportGroup, []))
            else:
                for sportGroup in thismodule_SportGroup_list:
                    BDsportIDs.extend(sportGroup_sportIDs_UImap_dict.get(sportGroup, []))
            # print(f"sportid 1 is ,",BDsportIDs)
            for sport in BDsportIDs:  # for each sport of current looping module,  #eg [1,2,54,55]
                if sport in betDelay_Severest_dict:  # compare BD of this sport with  mostSevere BD get so far. replace it if BD of this sport is hihger
                    if betDelay_Severest_dict[sport] < Module_BetDelay:
                        betDelay_Severest_dict[sport] = Module_BetDelay
                else:  # if no most severe yet, add this as most severe
                    betDelay_Severest_dict[sport] = Module_BetDelay
                # print(f"severest sport is ,",betDelay_Severest_dict)

        # only for crossModuleType: GBGood & hasEGON , saved (the only) EGON among moduleHits
        # if is_match(hitmodule['scr_gbRuleID'],11):
        if (hitObject.cross_GB_Good and hitObject.cross_has_EGON and is_match(hitmodule['scr_gbRuleID'], 11)):
            memCategory_of_directEGON = hitmodule['UpdateMemberCategory']
            isAdvised_of_directEGON = hitmodule['UpdateMemberIsAdvised']
            BetDelay_of_directEGON = thismodule_SportGroup_list

    return smallest_ranking_number_msp, smallest_ranking_number_spread, betDelay_Severest_dict, memCategory_of_directEGON, isAdvised_of_directEGON, BetDelay_of_directEGON


# @@changeCS:
def creditScore_application(smallest_rankNum, api_CalcBL_CSfinalBL_mapping, creditScore_before_hit):
    to_apply_creditScore = False
    # if CS is <=1  or dont have creditScore, no need apply creditScore, return newActionBL
    if not creditScore_before_hit or (creditScore_before_hit and creditScore_before_hit <= 1  ):  # @@change . see if there is a need to retrieve minCS from general setting
        return smallest_rankNum,to_apply_creditScore

    BL_ori_raw_percentage_value = MemberProfileSettingMappers.get_perc_by_ranking(smallest_rankNum)
    # for those that has no raw_percentage value, no need to apply creditScore. eg.Molly group, RMB1Group etc..return newActionBL
    if BL_ori_raw_percentage_value == None:
        return smallest_rankNum,to_apply_creditScore

    # retrieve the CS_finalBL rankNum if there is matching calculated_BL_raw_perc range
    calculated_BL_raw_perc = BL_ori_raw_percentage_value * creditScore_before_hit
    for mapping in api_CalcBL_CSfinalBL_mapping:
        # pass in argument(calculated_BL_raw_perc) into lambda function(that check if calculated_raw_BL is within defined range that map to CS_finalBL_ID)
        if mapping['func_within_defined_CalcBL_range'](float(calculated_BL_raw_perc)):
            return MemberProfileSettingMappers.get_ranking_by_ID(mapping['CS_finalBL_ID']),True #return newActionBL*CreditScore

    # if mapping between calculated_BL_raw_perc range and CS_FinalBL is not found/defined,  return newActionBL
    return smallest_rankNum,to_apply_creditScore




def BL_SG_Cross_Module_check(memSetting_before_hit, hitObject, smallest_rankNum, field_type):
    errMsg = None
    # this function is only used for special handling for EGON, so far
    if field_type == 'msp':
        value_before_hit = get_ranking_byID(memSetting_before_hit['sfMemberSettingProfileID'], 'msp')
        value_lastUpdatedBy, _ = parse_updatedby(memSetting_before_hit['sfMemberProfileSettingLastUpdatedBy'])
    else:
        value_before_hit = get_ranking_byID(memSetting_before_hit['sfSpreadGroupID'], 'spread')
        value_lastUpdatedBy, _ = parse_updatedby(memSetting_before_hit['sfSpreadGroupLastUpdatedBy'])

    # special handling for cross_GBBad_EGONGood
    # when upgrading(smallest_rankNum/most_severe_value  is better than existing value), lastupdatedby mz be EGON. if not dun take action.
    if (hitObject.cross_GBBad_EGONGood
            and smallest_rankNum > value_before_hit and value_lastUpdatedBy != 'GB_EGON'):
        errMsg = f'{field_type} only allowed to be upgraded if lastUpdby=EGON; behavour: {hitObject.cross_type}'
        smallest_rankNum = None
    return smallest_rankNum, errMsg


def BL_SG_Single_Module_check(memSetting_before_hit, hitObject, new_Hit_Action, smallest_rankNum, threshold_rankNum,
                              field_type):
    LastUpdatedby_system = False
    if field_type == 'msp':
        lastUpdatedBy, lastScoreType = parse_updatedby(memSetting_before_hit['sfMemberProfileSettingLastUpdatedBy'])
        isWithinValidityPeriod = memSetting_before_hit['msp_withinValidityPeriod']
        existing_valueID = memSetting_before_hit['sfMemberSettingProfileID']
    elif field_type == 'spread':
        lastUpdatedBy, lastScoreType = parse_updatedby(memSetting_before_hit['sfSpreadGroupLastUpdatedBy'])
        isWithinValidityPeriod = memSetting_before_hit['spread_withinValidityPeriod']
        existing_valueID = memSetting_before_hit['sfSpreadGroupID']

    if lastUpdatedBy and lastUpdatedBy.startswith('GB_') and not lastUpdatedBy.startswith('GB_MemberList'):
        LastUpdatedby_system = True

    # process Single EGON
    if hitObject.single_EGON:
        # if lastUpdby=DiffModule & withinValidityPeriod & prevScoreType=Bad, use severity btw existing & new hit value.
        # else remain(use newHit)
        if LastUpdatedby_system and not is_match(lastUpdatedBy,
                                                 hitObject.UpdBy_Module) and isWithinValidityPeriod == 1 and lastScoreType == 'Bad':
            smallest_rankNum = get_most_severe(get_ranking_byID(existing_valueID, field_type), smallest_rankNum)
            errMsg = f'{field_type} failed to use most severe value btw new & existing value. behaviour Hit: singleEGON & LastUpdby=diffModule & withinValidity & LastScoreType !=good'
        else:
            errMsg = f'{field_type} failed to be updated with EGON action'
    # process Single Non-EGON
    else:
        # Hit Single GBrule & lastUpdatedby=User/null
        if hitObject.hitGbRule and not LastUpdatedby_system:
            # if GoodScore,noAction allowed
            if is_match(new_Hit_Action['ScoreType'], 1):
                smallest_rankNum = None  # action is not allowed
                errMsg = f'update to {field_type} is not allowed for GoodScore and lastupdatedby is user/null'
            else:
                # (remove below in GBQAT-2384)
                # badScore & Action is less severe, then NOAction allowed
                # if is_GT(smallest_rankNum,threshold_rankNum):
                #     smallest_rankNum = None  # action is not allowed if badScore and newHit less severe than defaultValue
                #     errMsg = f'update to {field_type} is not allowed for BadScore and newHit less severe than threshold value'
                # else:
                #     errMsg = f'update to {field_type} has failed for  BadScore and newHit more severe than threshold value'

                # badScore , only downgrade is allowed(i.e get most sever between existing value vs newHit value)
                smallest_rankNum = get_most_severe(get_ranking_byID(existing_valueID, field_type), smallest_rankNum)
                errMsg = f'{field_type} can only downgrade from member existing value for BadScore,LastUpdby=user/null '


        # Hit SingleModule(GBrule & GBfeature) & LastUpdatedBy=DiffModule(due to reduce from cross)
        elif lastUpdatedBy and LastUpdatedby_system and not is_match(lastUpdatedBy, hitObject.UpdBy_Module):
            # if GoodScore,noAction allowed
            if is_match(new_Hit_Action['ScoreType'], 1):
                smallest_rankNum = None  # action is not allowed
                errMsg = f'update to {field_type} is not allowed for GoodScore and lastupdatedby is by diff Module'
            else:  # badScore & Within Validity period,then use most severe value between existing and new Hit
                # existing value is not possible to be Null/empty at this point
                if isWithinValidityPeriod == 1:  #
                    smallest_rankNum = get_most_severe(get_ranking_byID(existing_valueID, field_type), smallest_rankNum)
                    errMsg = f'{field_type} failed to use most severe value btw new & existing value. behaviour Hit: singleModule,LstUpdBy=DiffModule,withinValidtityPeriod '
                else:
                    errMsg = f'update to {field_type} has failed'
        else:
            errMsg = f'this test case is not covered, please check'
    return smallest_rankNum, errMsg


def get_threshold(hitObject, memSetting_before_hit, to_apply_creditScore,type):
    threshold_rankNum = None
    priorValue_UpdDate = memSetting_before_hit['revisedValueUpdatedDate']
    priorValue_Flag = memSetting_before_hit['isManualRevised']
    # if priorityflag is off on UI, isManualRevised will be set to 0 and PriorValue will be delete(None) in mysql.
    # so, we default priorflagUpdateDate to null to exclude checking in threshold
    if priorValue_Flag != 1:
        priorValue_UpdDate = None

    # !!! this part i hardcoded to cater for dirty data
    memSetting_before_hit['defaultSfMemberSettingProfileID'] = memSetting_before_hit[
        'defaultSfMemberSettingProfileID'] if memSetting_before_hit['defaultSfMemberSettingProfileID'] else 1
    memSetting_before_hit['revisedMemberProfileSettingID'] = memSetting_before_hit['revisedMemberProfileSettingID'] if (
                priorValue_UpdDate and memSetting_before_hit['revisedMemberProfileSettingID']) else 1
    memSetting_before_hit['defaultSfSpreadGroupID'] = memSetting_before_hit['defaultSfSpreadGroupID'] if \
    memSetting_before_hit['defaultSfSpreadGroupID'] else 1
    memSetting_before_hit['revisedSpreadGroupID'] = memSetting_before_hit['revisedSpreadGroupID'] if (
                priorValue_UpdDate and memSetting_before_hit['revisedSpreadGroupID']) else 1
    # !!!

    if type == 'msp':
        UserValue_UpdDate = memSetting_before_hit['sfMemberProfileSettingUpdatedDateByUser']
        MerchValue_UpdDate = memSetting_before_hit['sfMemberProfileSettingUpdatedDateByMerchant']
        UserValue_rankNum = get_ranking_byID(memSetting_before_hit['sfMemberProfileSettingIDUpdatedByUser'],
                                             'msp') if UserValue_UpdDate else None
        MerchValue_rankNum = get_ranking_byID(memSetting_before_hit['sfMemberProfileSettingIDUpdatedByMerchant'],
                                              'msp') if MerchValue_UpdDate else None
        PriorValue_rankNum = get_ranking_byID(
            memSetting_before_hit['revisedMemberProfileSettingID'], 'msp') if priorValue_UpdDate else None
        initial_rankNum = get_ranking_byID(
            memSetting_before_hit['defaultSfMemberSettingProfileID'], 'msp')
    else:
        UserValue_UpdDate = memSetting_before_hit['sfSpreadGroupUpdatedDateByUser']
        MerchValue_UpdDate = memSetting_before_hit['sfSpreadGroupUpdatedDateByMerchant']
        UserValue_rankNum = get_ranking_byID(
            memSetting_before_hit['sfSpreadGroupIDUpdatedByUser'], 'spread') if UserValue_UpdDate else None
        MerchValue_rankNum = get_ranking_byID(
            memSetting_before_hit['sfSpreadGroupIDUpdatedByMerchant'], 'spread') if MerchValue_UpdDate else None
        PriorValue_rankNum = get_ranking_byID(
            memSetting_before_hit['revisedSpreadGroupID'], 'spread') if priorValue_UpdDate else None
        initial_rankNum = get_ranking_byID(memSetting_before_hit['defaultSfSpreadGroupID'], 'spread')


    # =======GET THRESHOLD VALUE===================

    # if got CreditScore, apply merchant limit or prioritise Flag ===  @@changeCS: this part should be done
    if (to_apply_creditScore == True and type == 'msp'):
        if(priorValue_UpdDate or MerchValue_UpdDate):  #apply threshold if there is, else no threshold
            candidates = []
            if priorValue_UpdDate:  # save down for further check only if flag is on, value exists and date exists
                candidates.append((priorValue_UpdDate, PriorValue_rankNum))
            if MerchValue_UpdDate:
                candidates.append((MerchValue_UpdDate, MerchValue_rankNum))
            _, threshold_rankNum = max(candidates, key=lambda x: x[0])
    # if no CreditScore, type of threshold accordingly depends on single/cross type
    else:
        # for  (1)singleEGON or (2)GBgood_hasEGON or  or (3)GBbad_EGONbad,
        #      use priorFlag or merchantValue(whichever latest) as cap
        if (hitObject.single_EGON or hitObject.cross_GBGood_hasEGON or hitObject.cross_GBBad_EGONBad):
            if (priorValue_UpdDate or MerchValue_UpdDate): #apply threshold if got, else No threshold
                candidates = []
                if priorValue_UpdDate:  # save down for further check only if flag is on, value exists and date exists
                    candidates.append((priorValue_UpdDate, PriorValue_rankNum))
                if MerchValue_UpdDate:
                    candidates.append((MerchValue_UpdDate, MerchValue_rankNum))
                _, threshold_rankNum = max(candidates, key=lambda x: x[0])
        # for (4)singleGBrule;SingleGBfeature or (5)GBonly_good (6)crossGBonly_bad ,
        #      use UserValue or PrioritiseValue(whichever latest) as cap
        elif ((hitObject.singleModule and not hitObject.single_EGON) or hitObject.cross_onlyGBs_noEGON_GBGood or hitObject.cross_onlyGBs_noEGON_GBBad):
            if (UserValue_UpdDate or priorValue_UpdDate):  #apply threshold if there is, else initialValue
                candidates = []
                if UserValue_UpdDate:
                   candidates.append((UserValue_UpdDate, UserValue_rankNum))
                if priorValue_UpdDate:
                    candidates.append((priorValue_UpdDate, PriorValue_rankNum))
                _, threshold_rankNum = max(candidates, key=lambda x: x[0])
            else:
                threshold_rankNum = initial_rankNum
        # for (7)GBbad_egonGood,
        #     use UserValue or PrioritiseValue or MerchantValue(whichever latest)
        elif (hitObject.cross_GBBad_EGONGood):
            if (UserValue_UpdDate or priorValue_UpdDate or MerchValue_UpdDate): #apply threshold if there is, else initial value
                candidates = []
                if UserValue_UpdDate:
                    candidates.append((UserValue_UpdDate, UserValue_rankNum))
                if priorValue_UpdDate:
                    candidates.append((priorValue_UpdDate, PriorValue_rankNum))
                if MerchValue_UpdDate:
                    candidates.append((MerchValue_UpdDate, MerchValue_rankNum))
                _, threshold_rankNum = max(candidates, key=lambda x: x[0])
            else:
                threshold_rankNum = initial_rankNum


    return threshold_rankNum


'''
    # GET THRESHOLD VALUE
        #if singleEGON/GBgood_hasEGON, use merchantValue as cap
    if (  hitObject.single_EGON or hitObject.cross_GBGood_hasEGON  ) \
        and MerchValue_UpdDate:
        threshold_rankNum = MerchValue_rankNum
        # if singleGBrule/SingleGBfeature , use latest of UserValue or PrioritiseValue
    elif hitObject.singleModule and not hitObject.single_EGON  \
         and (UserValue_UpdDate or priorValue_UpdDate):
        candidates = []
        if UserValue_UpdDate:
            candidates.append((UserValue_UpdDate, UserValue_rankNum))
        if priorValue_UpdDate:
            candidates.append((priorValue_UpdDate, PriorValue_rankNum))
        _, threshold_rankNum = max(candidates, key=lambda x: x[0])
        # if crossGBonly/GBbad_EgonBad , use latest of UserValue or PrioritiseValue or MerchantValue
    elif hitObject.cross_onlyGBs_noEGON or hitObject.cross_GBBad_EGONBad or hitObject.cross_GBBad_EGONGood \
        and (UserValue_UpdDate or PriorValue_rankNum or MerchValue_UpdDate):
        candidates = []
        if UserValue_UpdDate:
            candidates.append((UserValue_UpdDate, UserValue_rankNum))
        if priorValue_UpdDate:
            candidates.append((priorValue_UpdDate, PriorValue_rankNum))
        if MerchValue_UpdDate:
            candidates.append((MerchValue_UpdDate, MerchValue_rankNum))
        _, threshold_rankNum = max(candidates, key=lambda x: x[0])
        # if required Uservalue/Prioritise/Merchant is not available, use value upon creation
    else:
        threshold_rankNum = initial_rankNum
'''


# # get threshold value(latest of userManualUpd or prioritisedValue. if both N/A, use value uponCreation)
# if UserValue_UpdDate and priorValue_UpdDate:  # has both userManual & prioritiseFlag
#     threshold_rankNum = UserValue_rankNum if UserValue_UpdDate > priorValue_UpdDate else PriorValue_rankNum
# elif UserValue_UpdDate:  # has userManual
#     threshold_rankNum = UserValue_rankNum
# elif priorValue_UpdDate:  # has prioritiseFlag
#     threshold_rankNum = PriorValue_rankNum
# else:  # has no userManualUpd & prioritisedFlag, then use value uponCreation
#     threshold_rankNum = initial_rankNum
