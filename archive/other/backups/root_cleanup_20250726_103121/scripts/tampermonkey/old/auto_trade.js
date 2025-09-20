function autoTrade(inputSymbol, quantity = 1, action = 'Buy', takeProfitTicks = 20, stopLossTicks = 10, tickSize = 0.25) {
  const marketData = getMarketData(inputSymbol);
  if (!marketData) {
    console.error(`Could not find market data for symbol: ${inputSymbol}`);
    return null;
  }
  
  console.log(`Found market data for ${marketData.symbol}:`);
  console.log(`Last Price: ${marketData.lastPrice}, Bid: ${marketData.bidPrice}, Offer: ${marketData.offerPrice}`);
  
  if (action !== 'Buy' && action !== 'Sell') {
    console.error(`Invalid action: ${action}. Must be either 'Buy' or 'Sell'`);
    return null;
  }
  
  // Use the entry price once and reuse it throughout
  const entryPrice = parseFloat(action === 'Buy' ? marketData.offerPrice : marketData.bidPrice);
  
  let stopLossPrice, takeProfitPrice;
  if (action === 'Buy') {
    stopLossPrice = (entryPrice - (stopLossTicks * tickSize)).toFixed(2);
    takeProfitPrice = (entryPrice + (takeProfitTicks * tickSize)).toFixed(2);
  } else {
    stopLossPrice = (entryPrice + (stopLossTicks * tickSize)).toFixed(2);
    takeProfitPrice = (entryPrice - (takeProfitTicks * tickSize)).toFixed(2);
  }
  
  console.log('Placing order with the following parameters:');
  console.log(`Symbol: ${marketData.symbol}, Action: ${action}, Entry Price: ${entryPrice.toFixed(2)}`);
  console.log(`Stop Loss: ${stopLossPrice} (${stopLossTicks} ticks), Take Profit: ${takeProfitPrice} (${takeProfitTicks} ticks)`);
  
  const tradeData = {
    symbol: marketData.symbol,
    action: action,
    qty: quantity.toString(),
    price: entryPrice.toFixed(2),
    takeProfit: takeProfitPrice,
    stopLoss: stopLossPrice,
  };
  
  createBracketOrdersManual(tradeData);
  return tradeData;
}


// Example usage
// autoTrade('NQ', 1); // Default: Buy, 10 ticks SL, 20 ticks TP, 0.25 tick size
autoTrade('NQ', 1, 'Sell', 50, 10, 0.25); // Buy with custom parameters
// autoTrade('NQ', 1, 'Sell', 8, 16, 0.25); // Sell with custom parameters

// To use this script, you need to import the functions from get_symbol_data.js and execute_trades.js
// or make sure they're loaded in the global scope before running this script.