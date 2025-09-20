from datetime import datetime

def get_current_contract(symbol):
    """
    Get the current contract symbol based on the provided symbol.
    
    Args:
        symbol (str): The base symbol to convert
        
    Returns:
        str: The current contract symbol
    """
    # Full list of month codes for futures contracts
    month_codes = {1: 'F', 2: 'G', 3: 'H', 4: 'J', 5: 'K', 6: 'M', 
                   7: 'N', 8: 'Q', 9: 'U', 10: 'V', 11: 'X', 12: 'Z'}
    
    current_month = datetime.now().month
    current_year = datetime.now().year

    # Increment month to get the next month contract
    next_month = current_month + 1
    if next_month > 12:
        next_month = 1
        current_year += 1

    # Handle '1!' case
    if '1!' in symbol:
        contract_code = month_codes[next_month]
        return f"{symbol.replace('1!', contract_code)}{str(current_year)[-1]}"

    # Handle explicit contracts like 'CLF2025'
    for month_code in month_codes.values():
        if month_code in symbol:
            # Convert year format 'YYYY' to a single digit year 'Y'
            year_suffix = symbol[-4:]
            if year_suffix.isdigit() and len(year_suffix) == 4:
                year_suffix = year_suffix[-1]
                return f"{symbol[:-4]}{year_suffix}"

    return symbol
