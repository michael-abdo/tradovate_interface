// Function to get account summary data
function getAllAccountTableData() {
  // The accounts data is in the third .publicDataTable_main element
  const tables = document.querySelectorAll('.public_fixedDataTable_main');
  
  // Look for the table with account headers
  let accountTable = null;
  for (let i = 0; i < tables.length; i++) {
    const table = tables[i];
    const headers = [...table.querySelectorAll('[role="columnheader"]')].map(h => 
      h.textContent.trim()
    );
    
    // Check if this table has account-related headers
    if (headers.includes('Account ▲') || headers.includes('Total Available Margin')) {
      accountTable = table;
      break;
    }
  }
  
  if (!accountTable) {
    return JSON.stringify([]);
  }
  
  // Extract headers
  const headers = [...accountTable.querySelectorAll('[role="columnheader"]')];
  const headerNames = headers.map(h => {
    // Clean up header text and remove arrow symbols
    let headerText = h.textContent.replace(/\s+/g, ' ').trim();
    
    // Remove arrow symbols (▲ or ▼)
    headerText = headerText.replace(/[\u25b2\u25bc]/, '').trim();
    
    // Standardize common header names
    const standardHeaders = {
      'Account': 'Account',
      'Dollar Open P L': 'Open P&L',
      'Dist Drawdown Net Liq': 'Net Liquidation',
      'Total Available Margin': 'Available Margin',
      'User': 'Phase',
      'Dollar Total P L': 'Total P&L',
      'Strategy': 'Strategy'
    };
    
    return standardHeaders[headerText] || headerText;
  });
  
  // Extract rows
  const rows = [...accountTable.querySelectorAll('.public_fixedDataTable_bodyRow')];
  
  const result = rows.map(r => {
    const cells = r.querySelectorAll('[role="gridcell"]');
    const rowData = {};
    
    headerNames.forEach((name, idx) => {
      if (idx < cells.length) {
        let text = cells[idx]?.innerText?.trim() || '';
        
        // Convert currency values to numbers
        if (typeof text === 'string' && text.startsWith('$')) {
          try {
            // Replace $ and commas, then convert to number
            text = Number(text.replace(/[$,]/g, '')) || 0;
          } catch (e) {
            // Keep error logging for critical errors
            console.error("Error converting currency:", e);
          }
        }
        
        rowData[name] = text;
      }
    });
    
    // Parse Status from Phase column and clean up Phase display
    if (rowData['Phase']) {
      // Extract status (active/inactive) from Phase text
      const phaseText = rowData['Phase'].toString().toLowerCase();
      if (phaseText.includes('active')) {
        rowData['Status'] = phaseText.includes('inactive') ? 'Inactive' : 'Active';
        
        // Clean up Phase to show only the number
        const phaseMatch = rowData['Phase'].match(/(\d+)/);
        if (phaseMatch) {
          rowData['Phase'] = phaseMatch[1];
        }
      } else {
        rowData['Status'] = 'Unknown';
      }
    } else {
      rowData['Status'] = 'Unknown';
    }
    
    // Determine platform based on account name
    const accountName = rowData['Account'] || '';
    const accountNameLower = accountName.toString().toLowerCase();
    
    // Dictionary of platform keywords and corresponding platform names
    const platformKeywords = {
      'demo': 'Tradovate',
      'tv': 'Tradovate',
      'tradovate': 'Tradovate',
      'apex': 'Apex',
      'pa': 'Apex',
      'amp': 'AMP',
      'ninja': 'NinjaTrader',
      'nt': 'NinjaTrader',
      'tt': 'TT',
      'trailing': 'TrailingTie'
    };
    
    // Check for platform keywords in account name
    let platform = 'Unknown';
    for (const [keyword, platformName] of Object.entries(platformKeywords)) {
      if (accountNameLower.includes(keyword)) {
        platform = platformName;
        break;
      }
    }
    
    rowData['Platform'] = platform;
    
    return rowData;
  });
  
  return JSON.stringify(result);
}