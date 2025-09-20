from datetime import datetime

dates = [
    "2025-06-08",  # MC7M25
    "2025-06-10",  # MC2M25  
    "2025-07-03",  # MC6N25
    "2025-07-07",  # Today
]

for date_str in dates:
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    day_name = dt.strftime("%A")
    day_num = dt.weekday()  # 0=Mon, 6=Sun
    print(f"{date_str} ({day_name}) - weekday number: {day_num}")