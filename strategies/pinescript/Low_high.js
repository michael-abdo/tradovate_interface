//@version=6
//#region Strategy Declaration
strategyName = "L/H"
strategy(strategyName, initial_capital=10000000, overlay=true, default_qty_type=strategy.fixed, default_qty_value=5, pyramiding=1,slippage=5,commission_type=strategy.commission.cash_per_contract,commission_value = 1.55)
//#endregion

//#region User Inputs
//––Lookbacks
lookback_low1  = input.int(500, minval=1, title="Lookback L1")
lookback_low2  = input.int(70,  minval=1, title="Lookback L2")
lookback_high1 = input.int(500, minval=1, title="Lookback H1")
lookback_high2 = input.int(70,  minval=1, title="Lookback H2")

//––Line selection
entry_line = input.string(title="Select Entry Line", options=["L1","L2","H1","H2"], defval="L2")
exit_line  = input.string(title="Select Exit Line",  options=["L1","L2","H1","H2"], defval="H2")

//––Direction dropdown
entry_dir  = input.string(title="Entry Direction",   options=["Long","Short"],       defval="Long")

//––Alerts
alert_entry = input.bool(true,  title="Enable Alert for Entry")
alert_exit  = input.bool(true,  title="Enable Alert for Exit")

//––Trading window (PST)
startTimeInput = input.time(title="Trading Start", defval=timestamp("2025-04-28 08:00"))
endTimeInput   = input.time(title="Trading End",   defval=timestamp("2025-04-28 14:00"))
//#endregion

//#region Time Filter
spansMultipleDays = endTimeInput < startTimeInput
adjustedEndTime   = spansMultipleDays ? endTimeInput + 24*60*60*1000 : endTimeInput
isInTradingTime   = (time >= startTimeInput) and (time < adjustedEndTime)
//#endregion

//#region Level Calculations
current_y1  = ta.lowest(close,  lookback_low1)
current_y2  = ta.lowest(close,  lookback_low2)
current_hy1 = ta.highest(close, lookback_high1)
current_hy2 = ta.highest(close, lookback_high2)

prev_y1  = current_y1[1]
prev_y2  = current_y2[1]
prev_hy1 = current_hy1[1]
prev_hy2 = current_hy2[1]
//#endregion

//#region Plot Levels
plot(current_y1,  color=color.new(color.red,   0), style=plot.style_stepline, linewidth=3, title="L1", display=display.all-display.price_scale-display.status_line)
plot(current_y2,  color=color.new(color.red,  30), style=plot.style_stepline, linewidth=2, title="L2", display=display.all-display.price_scale-display.status_line)
plot(current_hy1, color=color.new(color.green, 0), style=plot.style_stepline, linewidth=3, title="H1", display=display.all-display.price_scale-display.status_line)
plot(current_hy2, color=color.new(color.green,30), style=plot.style_stepline, linewidth=2, title="H2", display=display.all-display.price_scale-display.status_line)
//#endregion

//#region Helper Functions
get_selected_level(sel) =>
    switch sel
        "L1" => current_y1
        "L2" => current_y2
        "H1" => current_hy1
        "H2" => current_hy2
        => current_y1

get_selected_prev(sel) =>
    switch sel
        "L1" => prev_y1
        "L2" => prev_y2
        "H1" => prev_hy1
        "H2" => prev_hy2
        => prev_y1
//#endregion

//#region Entry/Exit Logic
selected_entry_level      = get_selected_level(entry_line)
selected_prev_entry_level = get_selected_prev(entry_line)

selected_exit_level       = get_selected_level(exit_line)
selected_prev_exit_level  = get_selected_prev(exit_line)   // NEW

entry_condition = entry_dir == "Long"  ? ta.crossunder(close, selected_prev_entry_level)
                                       : ta.crossover( close, selected_prev_entry_level)

exit_condition  = entry_dir == "Long"  ? ta.crossover( close, selected_prev_exit_level)  // use *prev* level
                                       : ta.crossunder(close, selected_prev_exit_level)
//#endregion


//#region Orders & Alerts
if isInTradingTime
    if entry_condition
        if alert_entry
            alert(str.format("{0} Entry Condition Met!", entry_dir), alert.freq_once_per_bar)
        strategy.entry("Main", entry_dir == "Long" ? strategy.long : strategy.short)

    if exit_condition
        if alert_exit
            alert(str.format("{0} Exit Condition Met!", entry_dir), alert.freq_once_per_bar)
        strategy.close("Main")
//#endregion