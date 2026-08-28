

pairs = {
    'byUser': 'yes',
    'memberSettingProfileID': 1,
    'spreadGroupID': 1,
    'RealSocBD': 0,
    'RealBbBD': 0,
    'CyberBD': 0,
    'OthersBD': 0,
    'memberCategoryID': 999,
    'isAdvised': 999,
    'memberProfileGroupID': None,
    'isManualRevised': 999
}

betDelaySportGroupList = []
sport_groups = [
    (1001, "Real Soccer", "RealSocBD"),
    (1002, "Real Basketball", "RealBbBD"),
    (1003, "Cyber Soccer and Cyber Basketball", "CyberBD"),
    (1000, "All Other Sports", "OthersBD"),
]

for sport_group_id, sport_group_name, pair_key in sport_groups:
    if pairs[pair_key] != 999:
        betDelaySportGroupList.append({
            "sportGroupID": sport_group_id,
            "sportGroupName": sport_group_name,
            "gbMemberBetDelay": pairs[pair_key],
            "updatedAt": mem_details['maxUpdatedAt']
        })


print(betDelaySportGroupList)