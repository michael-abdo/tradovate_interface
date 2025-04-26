// Function to get account summary data
function getAllAccountTableData() {
  console.log("getAllAccountTableData function called");
  
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
      console.log(`Found account table at index ${i}`);
      break;
    }
  }
  
  if (!accountTable) {
    console.log("No account table found");
    return JSON.stringify([]);
  }
  
  // Extract headers
  const headers = [...accountTable.querySelectorAll('[role="columnheader"]')];
  const headerNames = headers.map(h => 
    h.textContent.replace(/\s+/g, ' ').trim()
  );
  console.log("Headers:", headerNames);
  
  // Extract rows
  const rows = [...accountTable.querySelectorAll('.public_fixedDataTable_bodyRow')];
  console.log(`Found ${rows.length} account rows`);
  
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
            console.error("Error converting currency:", e);
          }
        }
        
        rowData[name] = text;
      }
    });
    
    return rowData;
  });
  
  console.log("Final result:", result);
  return JSON.stringify(result);
}