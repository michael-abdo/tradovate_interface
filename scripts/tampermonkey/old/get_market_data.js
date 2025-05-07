function getMarketData(inputSymbol) {
  // Map shorthand input to full symbol if necessary
  const symbolMap = { NQ: 'NQM5' };
  const symbol = symbolMap[inputSymbol] || inputSymbol;
  
  // Find all rows in the market data table
  const rows = document.querySelectorAll('.fixedDataTableRowLayout_rowWrapper');
  for (let row of rows) {
    const symbolEl = row.querySelector('.symbol-main');
    if (symbolEl && symbolEl.textContent.trim() === symbol) {
      const cells = row.querySelectorAll('.public_fixedDataTableCell_cellContent');
      return {
        symbol: symbol,
        lastPrice: cells[1] ? cells[1].textContent.trim() : '',
        change: cells[2] ? cells[2].textContent.trim() : '',
        percentChange: cells[3] ? cells[3].textContent.trim() : '',
        bidPrice: cells[4] ? cells[4].textContent.trim() : '',
        offerPrice: cells[5] ? cells[5].textContent.trim() : '',
        open: cells[6] ? cells[6].textContent.trim() : '',
        high: cells[7] ? cells[7].textContent.trim() : '',
        low: cells[8] ? cells[8].textContent.trim() : '',
        totalVolume: cells[9] ? cells[9].textContent.trim() : ''
      };
    }
  }
  return null;
}
