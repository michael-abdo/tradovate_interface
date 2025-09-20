# Risk Analysis (Who Has More Skin in the Game?)

## Philosophy & Meaning

The **Risk Analysis** examines institutional positioning by analyzing the dollar risk exposure of call and put holders across the options chain. This analysis answers the critical question: "Who has more to lose?" and identifies where institutional players will likely defend their positions.

### Core Philosophy
- **Risk Exposure Focus**: Calculate actual dollar amounts at risk for both bulls and bears
- **Battle Zone Identification**: Find strike prices where large amounts of capital are at risk
- **Institutional Behavior**: Large position holders will defend their strikes, creating support/resistance
- **Directional Bias**: Overall risk imbalance reveals market pressure and likely direction

### Key Concepts
1. **Call Risk (Bull Risk)**: Total premium paid by call buyers that would be lost if price stays below strikes
2. **Put Risk (Bear Risk)**: Total premium paid by put buyers that would be lost if price stays above strikes
3. **Battle Zones**: Strikes with highest combined risk where fierce price battles occur
4. **Risk Ratio**: The relative exposure between bulls and bears (e.g., 2:1 means one side has twice the risk)

### Trading Implications
- **Bulls Have More Risk**: Upward pressure expected, strikes act as magnets pulling price up
- **Bears Have More Risk**: Downward pressure expected, strikes act as magnets pulling price down
- **Battle Zones**: High volatility expected around these strikes as both sides fight
- **Risk Imbalance**: The greater the imbalance, the stronger the directional bias

## Trading Signals Generated
- **MARKET BIAS**: Overall directional pressure based on risk imbalance
- **BATTLE ZONES**: Critical strike levels with urgency ratings
- **DOMINANCE ANALYSIS**: Which side controls specific price ranges
- **KEY SIGNALS**: Specific actionable insights based on risk distribution

## Integration Role
This analysis provides crucial supplementary context to the primary Expected Value algorithm by revealing where institutional players are positioned and where they'll likely defend, helping to validate or challenge EV-based trade directions.

---

## Risk Analysis (Skin in the Game) - Pseudocode

```pseudocode
PROGRAM Risk_Analysis_Who_Has_More_Skin_In_The_Game

// ============================================================================
// CONSTANTS AND CONFIGURATION
// ============================================================================

CONSTANTS:
    CONTRACT_MULTIPLIER = 20  // NQ futures multiplier
    SIGNIFICANCE_THRESHOLD = 10000  // Minimum dollar risk to be considered significant
    BATTLE_ZONE_THRESHOLD = 0.15  // 15% of total risk to qualify as battle zone
    
    RISK_CATEGORIES = {
        EXTREME_CALL_DOMINANCE: 3.0,    // Bulls have 3x+ more risk
        STRONG_CALL_DOMINANCE: 2.0,     // Bulls have 2-3x more risk
        MODERATE_CALL_DOMINANCE: 1.5,   // Bulls have 1.5-2x more risk
        BALANCED: 1.2,                  // Risk within 20% of each other
        MODERATE_PUT_DOMINANCE: 0.67,   // Bears have 1.5-2x more risk
        STRONG_PUT_DOMINANCE: 0.5,      // Bears have 2-3x more risk
        EXTREME_PUT_DOMINANCE: 0.33     // Bears have 3x+ more risk
    }

// ============================================================================
// DATA STRUCTURES
// ============================================================================

STRUCTURE StrikeRisk:
    strike_price: FLOAT
    call_risk: FLOAT      // Dollar amount at risk for call holders
    put_risk: FLOAT       // Dollar amount at risk for put holders
    total_risk: FLOAT     // Combined risk at this strike
    dominance: STRING     // "BULL", "BEAR", or "NEUTRAL"
    risk_ratio: FLOAT     // Call risk / Put risk
END STRUCTURE

STRUCTURE BattleZone:
    strike: FLOAT
    type: STRING          // "CALL_HEAVY", "PUT_HEAVY", "CONTESTED"
    risk_amount: FLOAT
    percentage_of_total: FLOAT
    urgency: STRING       // "CRITICAL", "HIGH", "MODERATE"
    distance_from_current: FLOAT
END STRUCTURE

STRUCTURE RiskAnalysisResult:
    total_call_risk: FLOAT
    total_put_risk: FLOAT
    risk_ratio: FLOAT
    market_bias: STRING
    verdict: STRING
    battle_zones: ARRAY[BattleZone]
    strike_analysis: ARRAY[StrikeRisk]
    key_signals: ARRAY[STRING]
END STRUCTURE

// ============================================================================
// MAIN ANALYSIS FUNCTION
// ============================================================================

FUNCTION analyze_risk(options_data, current_price):
    // Step 1: Calculate risk at each strike
    strike_risks = calculate_strike_risks(options_data)
    
    // Step 2: Calculate total market risk
    total_risks = calculate_total_risks(strike_risks)
    
    // Step 3: Identify battle zones
    battle_zones = identify_battle_zones(strike_risks, total_risks, current_price)
    
    // Step 4: Analyze dominance patterns
    dominance_analysis = analyze_dominance_patterns(strike_risks, current_price)
    
    // Step 5: Generate market verdict
    verdict = generate_market_verdict(total_risks, dominance_analysis)
    
    // Step 6: Generate key trading signals
    key_signals = generate_key_signals(battle_zones, dominance_analysis, verdict)
    
    // Step 7: Compile results
    result = RiskAnalysisResult()
    result.total_call_risk = total_risks.total_call_risk
    result.total_put_risk = total_risks.total_put_risk
    result.risk_ratio = total_risks.risk_ratio
    result.market_bias = verdict.bias
    result.verdict = verdict.summary
    result.battle_zones = battle_zones
    result.strike_analysis = strike_risks
    result.key_signals = key_signals
    
    RETURN result
END FUNCTION

// ============================================================================
// RISK CALCULATION FUNCTIONS
// ============================================================================

FUNCTION calculate_strike_risks(options_data):
    strike_risks = []
    
    FOR each option IN options_data:
        strike_risk = StrikeRisk()
        strike_risk.strike_price = option.strike_price
        
        // Calculate dollar risk (OI * Premium * Multiplier)
        strike_risk.call_risk = option.call_oi * option.call_premium * CONTRACT_MULTIPLIER
        strike_risk.put_risk = option.put_oi * option.put_premium * CONTRACT_MULTIPLIER
        strike_risk.total_risk = strike_risk.call_risk + strike_risk.put_risk
        
        // Determine dominance at this strike
        IF strike_risk.call_risk > strike_risk.put_risk * 1.2:
            strike_risk.dominance = "BULL"
        ELSE IF strike_risk.put_risk > strike_risk.call_risk * 1.2:
            strike_risk.dominance = "BEAR"
        ELSE:
            strike_risk.dominance = "NEUTRAL"
        END IF
        
        // Calculate risk ratio
        IF strike_risk.put_risk > 0:
            strike_risk.risk_ratio = strike_risk.call_risk / strike_risk.put_risk
        ELSE:
            strike_risk.risk_ratio = 999  // Infinite bull dominance
        END IF
        
        strike_risks.append(strike_risk)
    END FOR
    
    RETURN strike_risks
END FUNCTION

FUNCTION calculate_total_risks(strike_risks):
    total_call_risk = 0
    total_put_risk = 0
    
    FOR each strike IN strike_risks:
        total_call_risk += strike.call_risk
        total_put_risk += strike.put_risk
    END FOR
    
    risk_ratio = 0
    IF total_put_risk > 0:
        risk_ratio = total_call_risk / total_put_risk
    ELSE IF total_call_risk > 0:
        risk_ratio = 999  // Infinite bull dominance
    ELSE:
        risk_ratio = 1  // No risk on either side
    END IF
    
    RETURN {
        total_call_risk: total_call_risk,
        total_put_risk: total_put_risk,
        risk_ratio: risk_ratio,
        total_risk: total_call_risk + total_put_risk
    }
END FUNCTION

// ============================================================================
// BATTLE ZONE IDENTIFICATION
// ============================================================================

FUNCTION identify_battle_zones(strike_risks, total_risks, current_price):
    battle_zones = []
    total_market_risk = total_risks.total_risk
    
    // Sort strikes by total risk
    sorted_strikes = sort(strike_risks, key=lambda s: s.total_risk, reverse=True)
    
    FOR each strike IN sorted_strikes:
        IF strike.total_risk < SIGNIFICANCE_THRESHOLD:
            CONTINUE  // Skip insignificant strikes
        END IF
        
        percentage_of_total = strike.total_risk / total_market_risk
        
        IF percentage_of_total >= BATTLE_ZONE_THRESHOLD:
            zone = BattleZone()
            zone.strike = strike.strike_price
            zone.risk_amount = strike.total_risk
            zone.percentage_of_total = percentage_of_total
            zone.distance_from_current = abs(strike.strike_price - current_price)
            
            // Determine zone type
            IF strike.risk_ratio > 2.0:
                zone.type = "CALL_HEAVY"
            ELSE IF strike.risk_ratio < 0.5:
                zone.type = "PUT_HEAVY"
            ELSE:
                zone.type = "CONTESTED"
            END IF
            
            // Determine urgency based on distance from current price
            distance_percentage = zone.distance_from_current / current_price
            IF distance_percentage < 0.01:  // Within 1%
                zone.urgency = "CRITICAL"
            ELSE IF distance_percentage < 0.02:  // Within 2%
                zone.urgency = "HIGH"
            ELSE:
                zone.urgency = "MODERATE"
            END IF
            
            battle_zones.append(zone)
        END IF
    END FOR
    
    RETURN battle_zones
END FUNCTION

// ============================================================================
// DOMINANCE PATTERN ANALYSIS
// ============================================================================

FUNCTION analyze_dominance_patterns(strike_risks, current_price):
    above_price_strikes = []
    below_price_strikes = []
    at_money_strikes = []
    
    FOR each strike IN strike_risks:
        distance_pct = (strike.strike_price - current_price) / current_price
        
        IF distance_pct > 0.005:  // More than 0.5% above
            above_price_strikes.append(strike)
        ELSE IF distance_pct < -0.005:  // More than 0.5% below
            below_price_strikes.append(strike)
        ELSE:
            at_money_strikes.append(strike)
        END IF
    END FOR
    
    // Analyze each region
    above_analysis = analyze_region(above_price_strikes, "ABOVE")
    below_analysis = analyze_region(below_price_strikes, "BELOW")
    atm_analysis = analyze_region(at_money_strikes, "ATM")
    
    // Identify key patterns
    patterns = []
    
    IF above_analysis.dominant_side == "BULL" AND below_analysis.dominant_side == "BEAR":
        patterns.append("CLASSIC_BATTLE_FORMATION")
    END IF
    
    IF atm_analysis.total_risk > above_analysis.total_risk + below_analysis.total_risk:
        patterns.append("INTENSE_ATM_BATTLE")
    END IF
    
    IF above_analysis.dominant_side == "BEAR":
        patterns.append("HEAVY_RESISTANCE_ABOVE")
    END IF
    
    IF below_analysis.dominant_side == "BULL":
        patterns.append("STRONG_SUPPORT_BELOW")
    END IF
    
    RETURN {
        above: above_analysis,
        below: below_analysis,
        atm: atm_analysis,
        patterns: patterns
    }
END FUNCTION

FUNCTION analyze_region(strikes, region_name):
    total_call_risk = sum(s.call_risk FOR s IN strikes)
    total_put_risk = sum(s.put_risk FOR s IN strikes)
    total_risk = total_call_risk + total_put_risk
    
    dominant_side = "NEUTRAL"
    IF total_call_risk > total_put_risk * 1.5:
        dominant_side = "BULL"
    ELSE IF total_put_risk > total_call_risk * 1.5:
        dominant_side = "BEAR"
    END IF
    
    RETURN {
        region: region_name,
        total_call_risk: total_call_risk,
        total_put_risk: total_put_risk,
        total_risk: total_risk,
        dominant_side: dominant_side,
        risk_ratio: total_call_risk / total_put_risk IF total_put_risk > 0 ELSE 999
    }
END FUNCTION

// ============================================================================
// VERDICT GENERATION
// ============================================================================

FUNCTION generate_market_verdict(total_risks, dominance_analysis):
    risk_ratio = total_risks.risk_ratio
    
    // Determine overall bias
    IF risk_ratio >= RISK_CATEGORIES.EXTREME_CALL_DOMINANCE:
        bias = "EXTREME UPWARD PRESSURE"
        summary = "EXTREME CALL DOMINANCE - Bulls have overwhelming control"
    ELSE IF risk_ratio >= RISK_CATEGORIES.STRONG_CALL_DOMINANCE:
        bias = "STRONG UPWARD PRESSURE"
        summary = "STRONG CALL DOMINANCE - Bulls have much more to lose"
    ELSE IF risk_ratio >= RISK_CATEGORIES.MODERATE_CALL_DOMINANCE:
        bias = "MODERATE UPWARD PRESSURE"
        summary = "MODERATE CALL DOMINANCE - Bulls have more skin in the game"
    ELSE IF risk_ratio >= RISK_CATEGORIES.BALANCED:
        bias = "NEUTRAL - RANGE BOUND"
        summary = "BALANCED RISK - Expect choppy, range-bound action"
    ELSE IF risk_ratio >= RISK_CATEGORIES.MODERATE_PUT_DOMINANCE:
        bias = "MODERATE DOWNWARD PRESSURE"
        summary = "MODERATE PUT DOMINANCE - Bears have more skin in the game"
    ELSE IF risk_ratio >= RISK_CATEGORIES.STRONG_PUT_DOMINANCE:
        bias = "STRONG DOWNWARD PRESSURE"
        summary = "STRONG PUT DOMINANCE - Bears have much more to lose"
    ELSE:
        bias = "EXTREME DOWNWARD PRESSURE"
        summary = "EXTREME PUT DOMINANCE - Bears have overwhelming control"
    END IF
    
    // Adjust based on pattern analysis
    IF "INTENSE_ATM_BATTLE" IN dominance_analysis.patterns:
        summary += " | CAUTION: Intense battle at current levels"
    END IF
    
    IF "CLASSIC_BATTLE_FORMATION" IN dominance_analysis.patterns:
        summary += " | Classic positioning detected"
    END IF
    
    RETURN {
        bias: bias,
        summary: summary
    }
END FUNCTION

// ============================================================================
// SIGNAL GENERATION
// ============================================================================

FUNCTION generate_key_signals(battle_zones, dominance_analysis, verdict):
    signals = []
    
    // Signal 1: Primary directional bias
    signals.append("PRIMARY BIAS: " + verdict.bias)
    
    // Signal 2: Nearest battle zone
    IF len(battle_zones) > 0:
        nearest_zone = min(battle_zones, key=lambda z: z.distance_from_current)
        signal = "NEAREST BATTLE: " + str(nearest_zone.strike) + " (" + 
                nearest_zone.type + ", " + nearest_zone.urgency + ")"
        signals.append(signal)
    END IF
    
    // Signal 3: Risk concentration
    IF len(battle_zones) >= 3:
        signals.append("HIGH RISK CONCENTRATION - Multiple battle zones active")
    END IF
    
    // Signal 4: Pattern-based signals
    FOR pattern IN dominance_analysis.patterns:
        IF pattern == "HEAVY_RESISTANCE_ABOVE":
            signals.append("RESISTANCE WARNING: Bears heavily defending upside")
        ELSE IF pattern == "STRONG_SUPPORT_BELOW":
            signals.append("SUPPORT ALERT: Bulls heavily defending downside")
        ELSE IF pattern == "INTENSE_ATM_BATTLE":
            signals.append("ATM BATTLE: Expect high volatility at current levels")
        END IF
    END FOR
    
    // Signal 5: Proximity danger
    critical_zones = [z FOR z IN battle_zones IF z.urgency == "CRITICAL"]
    IF len(critical_zones) > 0:
        signals.append("PROXIMITY ALERT: " + str(len(critical_zones)) + 
                      " critical battle zones within 1% of current price")
    END IF
    
    RETURN signals
END FUNCTION

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

FUNCTION sum(array):
    total = 0
    FOR each element IN array:
        total += element
    END FOR
    RETURN total
END FUNCTION

FUNCTION min(array, key_function):
    IF len(array) == 0:
        RETURN null
    END IF
    
    min_element = array[0]
    min_value = key_function(min_element)
    
    FOR each element IN array[1:]:
        value = key_function(element)
        IF value < min_value:
            min_value = value
            min_element = element
        END IF
    END FOR
    
    RETURN min_element
END FUNCTION

FUNCTION sort(array, key_function, reverse=False):
    // Implementation of sorting algorithm
    // Returns sorted array based on key_function
    RETURN sorted_array
END FUNCTION

// ============================================================================
// MAIN PROGRAM EXECUTION
// ============================================================================

BEGIN MAIN:
    // Load options data
    options_data = load_options_data()
    current_price = get_current_price()
    
    // Run risk analysis
    risk_result = analyze_risk(options_data, current_price)
    
    // Display results
    PRINT "=== RISK ANALYSIS: WHO HAS MORE SKIN IN THE GAME? ==="
    PRINT "Current Price: " + current_price
    PRINT ""
    PRINT "TOTAL RISK EXPOSURE:"
    PRINT "  Bulls (Call Risk): $" + format_currency(risk_result.total_call_risk)
    PRINT "  Bears (Put Risk): $" + format_currency(risk_result.total_put_risk)
    PRINT "  Risk Ratio: " + format_ratio(risk_result.risk_ratio)
    PRINT ""
    PRINT "VERDICT: " + risk_result.verdict
    PRINT "BIAS: " + risk_result.market_bias
    PRINT ""
    PRINT "BATTLE ZONES:"
    FOR each zone IN risk_result.battle_zones:
        PRINT "  Strike " + zone.strike + ": $" + format_currency(zone.risk_amount) + 
              " (" + zone.type + ", " + zone.urgency + ")"
    END FOR
    PRINT ""
    PRINT "KEY SIGNALS:"
    FOR each signal IN risk_result.key_signals:
        PRINT "  • " + signal
    END FOR
END MAIN

END PROGRAM
```