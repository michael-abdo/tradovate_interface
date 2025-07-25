//@version=6

strategyName = 'Velocity Graph 4/26 v1'
strategy(strategyName, initial_capital=10000000, overlay=false, default_qty_type=strategy.fixed, default_qty_value=5, pyramiding=1,slippage=5,commission_type=strategy.commission.cash_per_contract,commission_value = 1.55)
// import TradingView/Strategy/3

//#region  ======== Trading-window inputs ======
startHour      = input.int(title='Start Hour (PST)',    defval=6,  minval=0, maxval=23, group="Trading-window inputs", inline="Time1")
startMinute    = input.int(title='Start Minute (PST)', defval=35, minval=0, maxval=59, group="Trading-window inputs", inline="Time1")
endHour        = input.int(title='End Hour (PST)',      defval=14, minval=0, maxval=23, group="Trading-window inputs", inline="Time2")
endMinute      = input.int(title='End Minute (PST)',    defval=0,  minval=0, maxval=59, group="Trading-window inputs", inline="Time2")

currentHourPST = hour(time, 'America/Los_Angeles')
currentMinPST  = minute(time, 'America/Los_Angeles')

startMins      = startHour * 60 + startMinute
endMins        = endHour   * 60 + endMinute
currentMinsPST = currentHourPST * 60 + currentMinPST

isInTradingTime = startMins <= endMins ?
                  currentMinsPST >= startMins and currentMinsPST < endMins :
                  currentMinsPST >= startMins or  currentMinsPST < endMins

bgcolor(isInTradingTime ? color.new(color.green, 90) : na, title='Trading Window Background', display=display.none)
//#endregion

//#region  ======== Daily auto-flat at 14:00 PST ======
flatTime = timestamp('America/Los_Angeles', year, month, dayofmonth, 14, 0) - 60*1000
if time >= flatTime and time < flatTime + 60*1000
    strategy.close_all(comment='Auto-close 13:59')
//#endregion






//#region  ======== Core inputs ======
emaShortLength  = input.int(defval=50,  title='EMA Short Length',      minval=1,    maxval=1000, group="Core inputs", inline="EMA")
emaLongLength   = input.int(defval=200, title='EMA Long Length',       minval=1,    maxval=2000, group="Core inputs", inline="EMA")
lookbackPeriod  = input.int(defval=600, title='Lookback Period',       minval=1,    maxval=10000, group="Core inputs", inline="MA")
movingAvgLength = input.int(defval=20,  title='Moving Average Length', minval=1,    maxval=500,   group="Core inputs", inline="MA")
minTangentRange = input.float(defval=0.001, title='Tangent Threshold', minval=0, maxval=1, step=0.001, group="Core inputs", inline="Distance")
maxValueDist = input.float(title='Max Value Distance', defval=0.5, minval=0.1, step=0.1, group="Core inputs", inline="Distance")
//#endregion

//#region  ======== Alert helper ======
sendAlertJson(action, tradeType, entryPrice, takeProfitPrice, orderQty, orderType) =>
    '{"action":"' + action + '","tradeType":"' + tradeType + '","symbol":"' + syminfo.ticker + '","orderQty":' + str.tostring(orderQty) + ',"orderType":"' + orderType + '","entryPrice":' + str.tostring(entryPrice) + ',"takeProfitPrice":' + str.tostring(takeProfitPrice) + ',"strategy":"' + strategyName + '"}'
//#endregion

//#region  ======== EMA-tangent machinery ======
emaLong       = ta.ema(close, emaLongLength)
emaTangent    = emaLong - emaLong[3]
emaTangentMA  = ta.ema(emaTangent, movingAvgLength)

var array<float> lows  = array.new_float()
var array<float> highs = array.new_float()

if math.abs(emaTangentMA) >= minTangentRange
    if emaTangentMA < 0
        array.push(lows, emaTangentMA)
        if array.size(lows) > lookbackPeriod
            array.shift(lows)
    else
        array.push(highs, emaTangentMA)
        if array.size(highs) > lookbackPeriod
            array.shift(highs)

lowestTangentValue    = array.size(lows)  > 0 ? array.min(lows)  : na
highestTangentValue   = array.size(highs) > 0 ? array.max(highs) : na
averageLowestTangent  = array.size(lows)  > 0 ? array.avg(lows)  : na
averageHighestTangent = array.size(highs) > 0 ? array.avg(highs) : na
//#endregion

//#region  ======== Rate-of-growth bands ======
bbLen   = input.int(defval=20,  title='Bollinger Bands Length',    minval=1, group="Rate-of-growth bands", inline="BB")
bbMult  = input.float(defval=2.0, title='Bollinger Bands Multiplier', step=0.1, group="Rate-of-growth bands", inline="BB")

diff      = emaTangent - emaTangentMA
rog       = (diff - diff[1]) * 10
rogEma    = ta.ema(rog, 14)
std       = ta.stdev(rog, bbLen)
upper_band = rogEma + bbMult * std
lower_band = rogEma - bbMult * std

plot(rog, title='Rate of Growth', color=rog > upper_band ? color.green : rog < lower_band ? color.red : color.new(color.gray, 60))
//#endregion

//#region  ======== Plotting ======
plot(emaTangent, title='EMA Tangent',               color=color.blue,            linewidth=1)
plot(averageLowestTangent, title='Avg Low EMA Tangent',  color=color.red,             linewidth=1)
plot(lowestTangentValue, title='Lowest EMA Tangent',     color=color.gray,            linewidth=1)
plot(averageHighestTangent, title='Avg High EMA Tangent', color=color.green,           linewidth=1)
plot(highestTangentValue, title='Highest EMA Tangent',    color=color.gray,            linewidth=1)
plot(emaTangentMA, title='EMA Tangent MA',          color=color.orange,          linewidth=2)

zeroLine = plot(0, title='Zero Line', color=color.gray, linewidth=1)
fill(zeroLine, plot(emaTangentMA), color=emaTangentMA >= 0 ? color.new(color.green, 90) : color.new(color.red, 90), title='EMA MA Fill')
//#endregion



//#region  ======== Consolidation (flat-slope) detector ======
slopeThreshold = input.float(defval=0.005, title='Slope Threshold', step=0.0001, group="Consolidation settings", inline="Slope")
tf1            = input.int(defval=60,   title='Long Lookback (15m)', minval=1, group="Consolidation settings")
tf2            = input.int(defval=20,   title='Mid Lookback (5m)',   minval=1, group="Consolidation settings")
tf3            = input.int(defval=5,    title='Short Lookback (now)',minval=1, group="Consolidation settings")

isFlat(src, n, t) =>
    math.abs(ta.sma(src - src[1], n)) < t

inConsolidation = isFlat(emaTangentMA, tf1, slopeThreshold) and
                  isFlat(emaTangentMA, tf2, slopeThreshold) and
                  isFlat(emaTangentMA, tf3, slopeThreshold)

plotshape(inConsolidation ? 0 : na, location=location.absolute, style=shape.circle, size=size.tiny, color=color.yellow, title='Flat MA Across TFs')

var int lastAlert = na

if inConsolidation and (na(lastAlert) or time - lastAlert >= 5 * 60 * 1000)
    alert('🔔 Flat Consolidation Zone Detected', alert.freq_once_per_bar)
    lastAlert := time
//#endregion






//#region  ======== Trend-completion flags ======
var bool trendCompleteLong  = true
var bool trendCompleteShort = true
//#endregion

//#region  ======== Risk parameters ======
profitTarget = input.float(defval=1600, title='Take Profit ($)', minval=0, group="Risk parameters", inline="P&SL")
stopLoss     = input.float(defval=800,  title='Stop Loss ($)',   minval=0, group="Risk parameters", inline="P&SL")
enableLongEntries  = input.bool(defval=false, title='Enable Long Entries',  group="Risk parameters", inline="Entries")
enableShortEntries = input.bool(defval=true, title='Enable Short Entries', group="Risk parameters", inline="Entries")
pointValue   = syminfo.pointvalue
//#endregion

//#region  ======== Initialize Variables for Entries & TP/SL ======
var float entryPriceLong       = na
var float takeProfitPriceLong  = na
var float stopLossPriceLong    = na
var float entryPriceShort      = na
var float takeProfitPriceShort = na
var float stopLossPriceShort   = na
int barsSinceEntryLong         = na
int barsSinceEntryShort        = na
//#endregion

//#region  ======== Criteria selector ======
criteriaChoice = input.string(    defval='Rebound',    title='Strategy',    options=['Velocity Push', 'Demo','Rebound'],    group="Criteria selector",    inline="Criteria")

getConditions() =>
    // ── Initialise outputs
    bool longE  = false, shortE  = false
    bool longX  = false, shortX  = false

    // ── Universal entry-permission rules
    enterLongUniversal  = enableLongEntries and isInTradingTime //and trendCompleteLong
    enterShortUniversal = enableShortEntries and isInTradingTime //and trendCompleteShort 

    // ── Universal exit rules (TP / SL)
    exitLongUniversal  = close >= takeProfitPriceLong  or close <= stopLossPriceLong
    exitShortUniversal = close <= takeProfitPriceShort or close >= stopLossPriceShort

    
    farHigh = (math.abs(highestTangentValue) - math.abs(averageHighestTangent)) > maxValueDist
    farLow  = (math.abs(lowestTangentValue)  - math.abs(averageLowestTangent))  > maxValueDist

    if criteriaChoice == 'Velocity Push'
        // ── Velocity Push logic
        tooHigh = math.abs(emaTangent - highestTangentValue) < minTangentRange
        tooLow  = math.abs(emaTangent - lowestTangentValue)  < minTangentRange

        longE := enterLongUniversal and ta.crossover(emaTangentMA, averageHighestTangent) and rog > upper_band/2 and
                 not tooHigh and not (emaTangent > highestTangentValue) and farHigh

        shortE := enterShortUniversal and ta.crossunder(emaTangentMA, averageLowestTangent) and rog < lower_band/2 and
                  not tooLow and not (emaTangent < lowestTangentValue) and farLow

        longX  := exitLongUniversal  or rog < lower_band or
                  ta.crossover(emaTangent, highestTangentValue) or
                  ta.crossunder(emaTangentMA, averageHighestTangent)

        shortX := exitShortUniversal or rog > upper_band or
                  ta.crossunder(emaTangent, lowestTangentValue) or
                  ta.crossover(emaTangentMA, averageLowestTangent)

    else if criteriaChoice == 'Demo'
        // ── Demo: EMA-tangent crossover
        longE  := enterLongUniversal  and ta.crossover(emaTangent, emaTangentMA)
        shortE := enterShortUniversal and ta.crossunder(emaTangent, emaTangentMA)

        longX  := exitLongUniversal  or ta.crossunder(emaTangent, emaTangentMA)
        shortX := exitShortUniversal or ta.crossover(emaTangent, emaTangentMA)

    else if criteriaChoice == 'Rebound'
        // ── Rebound logic ────────────────────────────────────────────
        halfHigh = (highestTangentValue + averageHighestTangent) / 2
        halfLow  = (lowestTangentValue  + averageLowestTangent)  / 2

        farHighRebound = math.abs(emaTangentMA - emaTangent) > maxValueDist
        farLowRebound  = math.abs(emaTangentMA - emaTangent) > maxValueDist

        rogSlopePositive = rog - rog[1] > 0
        rogSlopeNegative = rog - rog[1] < 0

        // ROG must have stayed inside BB channel for the last 5 bars
        rogInsideBand = rog[0] > lower_band[0] and rog[0] < upper_band[0] and        rog[1] > lower_band[1] and rog[1] < upper_band[1] and        rog[2] > lower_band[2] and rog[2] < upper_band[2] and        rog[3] > lower_band[3] and rog[3] < upper_band[3] and        rog[4] > lower_band[4] and rog[4] < upper_band[4] and        rog[5] > lower_band[5] and rog[5] < upper_band[5] and        rog[6] > lower_band[6] and rog[6] < upper_band[6] and        rog[7] > lower_band[7] and rog[7] < upper_band[7] and        rog[8] > lower_band[8] and rog[8] < upper_band[8] and        rog[9] > lower_band[9] and rog[9] < upper_band[9]
         //------------------------------------------------------------------

        // Long setup
        preSetupLong = emaTangentMA > halfHigh and emaTangent > averageHighestTangent
        pullbackLong = emaTangent   < emaTangentMA
        longE        := enterLongUniversal and preSetupLong and pullbackLong and farHighRebound and rog > 0 and rogInsideBand and rogSlopePositive

        // Short setup
        preSetupShort = emaTangentMA < halfLow and emaTangent < averageLowestTangent
        pullbackShort = emaTangent   > emaTangentMA
        shortE        := enterShortUniversal and preSetupShort and pullbackShort and farLowRebound and rog < 0 and rogInsideBand and rogSlopeNegative 

        // Exits
        longX  := exitLongUniversal  or ta.crossunder(emaTangent, averageHighestTangent) //or rog < lower_band
        shortX := exitShortUniversal or ta.crossover(emaTangent,  averageLowestTangent) //or rog > upper_band
        // ─────────────────────────────────────────────────────────────

    [longE, shortE, longX, shortX]

[isLongEntry, isShortEntry, exitLongCondition, exitShortCondition] = getConditions()
//#endregion


//#region  ======== Strategy Logic ======
if isLongEntry
    entryPriceLong       := close
    tpPts                = profitTarget/pointValue
    slPts                = stopLoss/pointValue
    takeProfitPriceLong  := entryPriceLong + tpPts*(1+0.002)
    stopLossPriceLong    := entryPriceLong - slPts*(1+0.002)
    trendCompleteLong    := false
    barsSinceEntryLong   := 0
    strategy.entry('Long', strategy.long, alert_message=sendAlertJson('Buy','Open',close,takeProfitPriceLong,1,'Market'), comment='TP '+str.tostring(takeProfitPriceLong))

if strategy.position_size > 0
    barsSinceEntryLong := nz(barsSinceEntryLong) + 1
    if exitLongCondition
        strategy.close('Long', alert_message=sendAlertJson('Sell','Close',close,0,1,'Market'), comment='Exit Long')
        trendCompleteLong    := true
        entryPriceLong       := na
        takeProfitPriceLong  := na
        stopLossPriceLong    := na
        barsSinceEntryLong   := 0

if isShortEntry
    entryPriceShort       := close
    tpPts                 = profitTarget/pointValue
    slPts                 = stopLoss/pointValue
    takeProfitPriceShort  := entryPriceShort - tpPts*(1+0.002)
    stopLossPriceShort    := entryPriceShort + slPts*(1+0.002)
    trendCompleteShort    := false
    barsSinceEntryShort   := 0
    strategy.entry('Short', strategy.short, alert_message=sendAlertJson('Sell','Open',close,takeProfitPriceShort,1,'Market'), comment='TP '+str.tostring(takeProfitPriceShort))

if strategy.position_size < 0
    barsSinceEntryShort := nz(barsSinceEntryShort) + 1
    if exitShortCondition
        strategy.close('Short', alert_message=sendAlertJson('Buy','Close',close,0,1,'Market'), comment='Exit Short')
        trendCompleteShort    := true
        entryPriceShort       := na
        takeProfitPriceShort  := na
        stopLossPriceShort    := na
        barsSinceEntryShort   := 0
//#endregion  