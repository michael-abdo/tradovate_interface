// Function to get account summary data with DOM Intelligence validation
function getAllAccountTableData() {
  console.log('🔍 DOM Intelligence: Starting getAllAccountTableData with validation');
  console.log('🔍 Current URL:', window.location.href);
  console.log('🔍 Document ready state:', document.readyState);
  
  // Check if we're on the right page
  if (!window.location.href.includes('tradovate')) {
    console.error('❌ Not on Tradovate page! URL:', window.location.href);
    return JSON.stringify([]);
  }
  
  // STEP 1: Validate that data tables exist
  console.log('🔍 Pre-validation: Checking for data tables');
  const tableSelectors = [
    '.public_fixedDataTable_main', 
    '.module.positions.data-table',
    '.positions .data-table',
    '.positions',
    '[role="table"]',
    '.fixedDataTable'
  ];
  let tableSelector = null;
  
  // Find which table selector actually works
  for (const selector of tableSelectors) {
    const element = document.querySelector(selector);
    if (element !== null) {
      console.log(`✅ Found table with selector: ${selector}`);
      tableSelector = selector;
      break;
    } else {
      console.warn(`❌ Element not found: ${selector}`);
    }
  }
  
  if (!tableSelector) {
    console.error('❌ No data tables found with any known selector');
    return JSON.stringify([]);
  }
  
  const tables = document.querySelectorAll(tableSelector);
  console.log(`✅ Found ${tables.length} data tables`);
  
  // Additional debugging - check what elements exist on the page
  console.log('🔍 Debug: Checking for any table-like elements on page');
  const debugSelectors = [
    'table',
    '[role="table"]',
    '.table',
    '.data-table',
    '.fixedDataTable',
    '.public_fixedDataTable_main',
    'div[class*="table"]',
    'div[class*="Table"]'
  ];
  
  for (const selector of debugSelectors) {
    const elements = document.querySelectorAll(selector);
    if (elements.length > 0) {
      console.log(`✅ Found ${elements.length} elements with selector: ${selector}`);
      if (elements.length <= 3) {
        elements.forEach((el, idx) => {
          console.log(`   Element ${idx}: ${el.tagName}, classes: ${el.className}`);
        });
      }
    }
  }
  
  // STEP 2: Look for the table with account headers with validation
  console.log('🔍 Pre-validation: Searching for account table headers');
  let accountTable = null;
  
  for (let i = 0; i < tables.length; i++) {
    const table = tables[i];
    
    // Validate table structure before accessing
    const headerSelector = '[role="columnheader"]';
    const tableHeaders = table.querySelectorAll(headerSelector);
    
    if (tableHeaders.length === 0) {
      console.warn(`⚠️ Table ${i} has no column headers, skipping`);
      continue;
    }
    
    console.log(`🔍 Validating table ${i} with ${tableHeaders.length} headers`);
    
    const headers = [...tableHeaders].map(h => {
      if (!h.textContent) {
        console.warn(`⚠️ Header element has no text content`);
        return '';
      }
      return h.textContent.trim();
    });
    
    console.log(`📋 Table ${i} headers:`, headers);
    
    // Check if this table has account-related headers (more flexible)
    const accountHeaders = headers.some(h => 
      h.toLowerCase().includes('account') || 
      h.toLowerCase().includes('margin') ||
      h.toLowerCase().includes('balance') ||
      h.toLowerCase().includes('equity') ||
      h.toLowerCase().includes('available') ||
      h.toLowerCase().includes('user')
    );
    
    if (accountHeaders) {
      console.log(`✅ Found account table at index ${i} with headers:`, headers);
      accountTable = table;
      break;
    } else {
      console.log(`❌ Table ${i} does not appear to be account table. Headers:`, headers);
    }
  }
  
  // STEP 3: Validate account table was found
  if (!accountTable) {
    console.error('❌ No account table found after checking all tables');
    console.log('📋 Available tables searched:', tables.length);
    console.log('📊 Page debugging info:');
    console.log('   - URL:', window.location.href);
    console.log('   - Title:', document.title);
    console.log('   - First 200 chars of body:', document.body.innerText.substring(0, 200));
    
    // Try to find ANY table and report what we see
    const anyTable = document.querySelector('table, [role="table"], .data-table, .table');
    if (anyTable) {
      console.log('   - Found a table-like element:', anyTable.tagName, anyTable.className);
    }
    
    return JSON.stringify([]);
  }
  
  console.log('✅ Pre-validation passed: Account table located');
  
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
  
  // STEP 4: Validate header extraction
  console.log('🔍 Pre-validation: Extracting headers');
  const tableHeaders = [...accountTable.querySelectorAll('[role="columnheader"]')];
  
  if (tableHeaders.length === 0) {
    console.error('❌ No headers found in account table');
    return JSON.stringify([]);
  }
  
  console.log(`✅ Found ${tableHeaders.length} headers in account table`);
  
  // STEP 5: Validate row extraction  
  console.log('🔍 Pre-validation: Extracting table rows');
  const rows = [...accountTable.querySelectorAll('.public_fixedDataTable_bodyRow')];
  
  if (rows.length === 0) {
    console.warn('⚠️ No data rows found in account table');
    return JSON.stringify([]);
  }
  
  console.log(`✅ Found ${rows.length} data rows in account table`);
  
  const result = rows.map((r, rowIndex) => {
    console.log(`🔍 Processing row ${rowIndex + 1}/${rows.length}`);
    
    // Validate row structure
    const cells = r.querySelectorAll('[role="gridcell"]');
    if (cells.length === 0) {
      console.warn(`⚠️ Row ${rowIndex} has no grid cells`);
      return {};
    }
    
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
  
  // STEP 6: Post-validation - Verify data extraction success
  console.log('🔍 Post-validation: Verifying extracted data');
  
  const validRows = result.filter(row => Object.keys(row).length > 0);
  if (validRows.length === 0) {
    console.error('❌ Post-validation failed: No valid account data extracted');
    return JSON.stringify([]);
  }
  
  console.log(`✅ Post-validation passed: ${validRows.length}/${result.length} valid account records extracted`);
  
  // Log sample of extracted data for verification
  if (validRows.length > 0) {
    console.log('📋 Sample extracted account data:', {
      sampleRecord: validRows[0],
      totalRecords: validRows.length,
      extractedFields: Object.keys(validRows[0])
    });
  }
  
  console.log('✅ DOM Intelligence: getAllAccountTableData completed successfully');
  return JSON.stringify(validRows);
}