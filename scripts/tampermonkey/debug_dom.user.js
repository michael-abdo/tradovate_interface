// Function to analyze the DOM structure of the Tradovate page
function analyzeTradovateDom() {
  const results = {
    tables: [],
    potentialAccountTables: [],
    publicDataTables: []
  };
  
  // Find all tables
  const allTables = document.querySelectorAll('table');
  results.tables = allTables.length;
  
  // Find all data tables (more likely to be account info)
  const dataTables = document.querySelectorAll('.data-table');
  
  dataTables.forEach((table, idx) => {
    results.potentialAccountTables.push({
      index: idx,
      className: table.className,
      childCount: table.children.length,
      headers: [...table.querySelectorAll('th, [role="columnheader"]')].map(h => h.textContent.trim())
    });
  });
  
  // Find all FixedDataTable elements (Tradovate specific)
  const fixedDataTables = document.querySelectorAll('.public_fixedDataTable_main');
  
  fixedDataTables.forEach((table, idx) => {
    // Get header information
    const headers = [...table.querySelectorAll('[role="columnheader"]')].map(h => h.textContent.trim());
    
    // Get row count
    const rows = table.querySelectorAll('.public_fixedDataTable_bodyRow');
    
    // Sample some cell data from the first row if available
    let sampleData = {};
    if (rows.length > 0) {
      const firstRow = rows[0];
      const cells = firstRow.querySelectorAll('[role="gridcell"]');
      
      headers.forEach((header, i) => {
        if (i < cells.length) {
          sampleData[header] = cells[i].innerText.trim();
        }
      });
    }
    
    results.publicDataTables.push({
      index: idx,
      position: {
        top: table.offsetTop,
        left: table.offsetLeft,
        width: table.offsetWidth,
        height: table.offsetHeight
      },
      headerCount: headers.length,
      headers: headers,
      rowCount: rows.length,
      sampleData: sampleData,
      isVisible: table.offsetParent !== null
    });
  });
  
  // Look for any specific account tables
  const accountsModule = document.querySelector('.module.accounts');
  if (accountsModule) {
    results.accountsModuleFound = true;
    results.accountsModuleInfo = {
      childCount: accountsModule.children.length,
      text: accountsModule.innerText.substring(0, 100) + '...'
    };
  } else {
    results.accountsModuleFound = false;
  }
  
  // Look for the sidebar where account info might be
  const sidebar = document.querySelector('.sidebar');
  if (sidebar) {
    results.sidebarFound = true;
    const sidebarTables = sidebar.querySelectorAll('.public_fixedDataTable_main');
    results.sidebarTableCount = sidebarTables.length;
    
    if (sidebarTables.length > 0) {
      const firstTable = sidebarTables[0];
      results.sidebarFirstTableHeaders = [...firstTable.querySelectorAll('[role="columnheader"]')].map(h => h.textContent.trim());
    }
  } else {
    results.sidebarFound = false;
  }
  
  // Get URL info to confirm we're on the right page
  results.url = window.location.href;
  results.title = document.title;
  
  return JSON.stringify(results, null, 2);
}