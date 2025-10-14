// Enhanced Order Feedback Data Structure
// This structure captures comprehensive order execution data for verification

const EnhancedOrderFeedback = {
    // Core order identification
    orderId: null,              // Primary order ID
    symbol: null,               // Trading symbol (e.g., "NQZ5")
    account: null,              // Account identifier
    
    // Order parameters
    action: null,               // "Buy" or "Sell"
    orderType: null,            // "MARKET", "LIMIT", "STOP", "STOP_LIMIT"
    quantity: null,             // Requested quantity
    requestedPrice: null,       // Limit price (null for market orders)
    timeInForce: null,          // "DAY", "GTC", "IOC", "FOK"
    
    // Execution details
    status: null,               // "FILLED", "PARTIAL", "REJECTED", "CANCELLED"
    fillRatio: null,            // e.g., "6/6" parsed to {filled: 6, total: 6}
    fills: [],                  // Array of individual fills
    /* Fill structure:
    {
        timestamp: null,
        price: null,
        quantity: null,
        venue: null,
        id: null
    }
    */
    
    // Price analysis
    averageFillPrice: null,     // Calculated from fills
    slippage: null,             // For market orders: fillPrice - midPrice at submission
    priceImprovement: null,     // For limit orders: limitPrice - fillPrice (positive = better)
    
    // Associated orders
    parentOrderId: null,        // For bracket orders
    stopLossOrderId: null,      // Associated stop loss
    takeProfitOrderId: null,    // Associated take profit
    
    // Timing metrics
    submittedAt: null,          // Order submission timestamp
    firstFillAt: null,          // First fill timestamp
    completedAt: null,          // Final fill/rejection timestamp
    timeToFill: null,           // completedAt - submittedAt (milliseconds)
    
    // Risk and cost
    riskCheckStatus: null,      // "PASSED", "FAILED", "BYPASSED"
    commission: null,           // Trading fees
    exchangeFees: null,         // Exchange fees
    totalCost: null,            // commission + fees
    
    // Rejection details
    rejectionReason: null,      // Specific rejection reason
    rejectionCode: null,        // Error code if available
    
    // Event history
    events: [],                 // All order events chronologically
    /* Event structure:
    {
        timestamp: null,
        id: null,
        type: null,         // "SUBMITTED", "RISK_PASSED", "FILLED", "REJECTED"
        description: null,
        details: {}         // Event-specific data
    }
    */
    
    // Raw data
    headerHTML: null,           // Trading ticket header HTML
    fullHTML: null,             // Complete order history HTML
    
    // Metadata
    capturedAt: null,           // When this feedback was captured
    version: "1.0"              // Structure version for compatibility
};

// Helper function to parse fill ratio
function parseFillRatio(ratioString) {
    // Parse "6/6" into {filled: 6, total: 6}
    const match = ratioString.match(/(\d+)\/(\d+)/);
    if (match) {
        return {
            filled: parseInt(match[1]),
            total: parseInt(match[2])
        };
    }
    return null;
}

// Helper function to calculate average fill price
function calculateAverageFillPrice(fills) {
    if (!fills || fills.length === 0) return null;
    
    let totalValue = 0;
    let totalQuantity = 0;
    
    fills.forEach(fill => {
        totalValue += fill.price * fill.quantity;
        totalQuantity += fill.quantity;
    });
    
    return totalQuantity > 0 ? totalValue / totalQuantity : null;
}

// Helper function to parse order type from header
function parseOrderType(headerText) {
    if (headerText.includes(' MKT ')) return 'MARKET';
    if (headerText.includes(' LMT ')) return 'LIMIT';
    if (headerText.includes(' STP ')) return 'STOP';
    if (headerText.includes(' STP LMT ')) return 'STOP_LIMIT';
    return 'UNKNOWN';
}

// Helper function to extract order details from header
function parseOrderHeader(headerElement) {
    const headerText = headerElement.textContent;
    
    // Extract order ID (e.g., "#289076630758")
    const orderIdMatch = headerText.match(/#(\d+)/);
    const orderId = orderIdMatch ? orderIdMatch[1] : null;
    
    // Extract symbol (e.g., "NQZ5")
    const symbolMatch = headerText.match(/([A-Z]+\d*)\s+(?:MKT|LMT|STP)/);
    const symbol = symbolMatch ? symbolMatch[1] : null;
    
    // Extract action (Buy/Sell)
    const action = headerText.includes('Buy') ? 'Buy' : 
                   headerText.includes('Sell') ? 'Sell' : null;
    
    // Extract quantity and fill ratio
    const quantityMatch = headerText.match(/(\d+)\s+[A-Z]+\d*\s+(?:MKT|LMT|STP)/);
    const quantity = quantityMatch ? parseInt(quantityMatch[1]) : null;
    
    // Extract fill ratio (e.g., "6/6")
    const fillRatioMatch = headerText.match(/(\d+\/\d+)/);
    const fillRatio = fillRatioMatch ? parseFillRatio(fillRatioMatch[1]) : null;
    
    // Extract status
    let status = 'UNKNOWN';
    if (headerText.includes('Filled')) status = 'FILLED';
    else if (headerText.includes('Partial')) status = 'PARTIAL';
    else if (headerText.includes('Rejected')) status = 'REJECTED';
    else if (headerText.includes('Cancelled')) status = 'CANCELLED';
    
    // Extract limit price if present
    const limitPriceMatch = headerText.match(/LMT at ([\d.]+)/);
    const limitPrice = limitPriceMatch ? parseFloat(limitPriceMatch[1]) : null;
    
    return {
        orderId,
        symbol,
        action,
        orderType: parseOrderType(headerText),
        quantity,
        requestedPrice: limitPrice,
        fillRatio,
        status
    };
}

// Export for use in autoOrder.user.js
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        EnhancedOrderFeedback,
        parseFillRatio,
        calculateAverageFillPrice,
        parseOrderType,
        parseOrderHeader
    };
}