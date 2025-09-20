#!/usr/bin/env python3
from datetime import datetime

# Check what day of week July 3, 2025 is
date = datetime(2025, 7, 3)
print(f"July 3, 2025 is a {date.strftime('%A')}")
print(f"Day of week number: {date.weekday()} (0=Monday, 6=Sunday)")

# Check July 7, 2025 (Monday)
date2 = datetime(2025, 7, 7)
print(f"\nJuly 7, 2025 is a {date2.strftime('%A')}")
print(f"Day of week number: {date2.weekday()}")

# Symbol analysis
print("\n--- SYMBOL ANALYSIS ---")
print("Based on the data files from July 3rd (Thursday):")
print("- MC6N25 was used (MC = Micro E-mini, 6 = ???, N = July, 25 = 2025)")
print("- MM6N25 was used (MM = E-mini, 6 = ???, N = July, 25 = 2025)")
print("\nIf standard day codes are 1=Mon, 2=Tue, 3=Wed, 4=Thu, 5=Fri")
print("Then 6 doesn't match Thursday (which should be 4)")
print("\nPossible explanations:")
print("1. Barchart uses different day codes (6 might mean something else)")
print("2. These are special weekly contracts that expire on a specific day")
print("3. The '6' might refer to the week number or some other designation")