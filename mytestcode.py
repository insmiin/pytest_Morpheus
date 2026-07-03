from datetime import datetime, timedelta, timezone

twenty_four_hours_ago = datetime.now(timezone.utc) - timedelta(hours=24)

print(twenty_four_hours_ago.strftime("%Y-%m-%d %H:%M:%S"))
print(twenty_four_hours_ago)
print(datetime.now(timezone.utc))
