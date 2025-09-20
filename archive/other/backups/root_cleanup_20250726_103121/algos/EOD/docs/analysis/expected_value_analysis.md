# Expected Value Analysis (NQ Options EV Algorithm)

## Philosophy & Meaning

The **Expected Value Analysis** is the **primary trading algorithm** for NQ Options, designed to identify high-probability trading opportunities by calculating the mathematical expected value of potential trades using weighted market factors.

### Core Philosophy
- **Mathematical Foundation**: Every trade decision must be backed by positive expected value (+EV)
- **Multi-Factor Weighting**: Combines Open Interest, Volume, Put/Call Ratio, and Distance to create a comprehensive probability model
- **Quality Over Quantity**: Strict quality criteria ensure only the best setups are considered
- **Risk-Adjusted Returns**: Incorporates risk/reward ratios to balance profit potential with downside protection

### Weighted Factors (Your Algorithm)
1. **Open Interest Factor (35%)** - Market commitment and liquidity depth
2. **Volume Factor (25%)** - Current market activity and conviction
3. **Put/Call Ratio Factor (25%)** - Sentiment and directional bias
4. **Distance Factor (15%)** - Proximity to current price for execution probability

### Quality Criteria
- **Minimum Expected Value**: 15 points
- **Minimum Probability**: 60%
- **Maximum Risk**: 150 points
- **Minimum Risk/Reward**: 1.0

## Trading Signals Generated
- **PRIMARY**: Best EV trade recommendations with entry, target, stop, and position sizing
- **QUALITY SETUPS**: List of all trades meeting minimum criteria
- **MARKET METRICS**: Overall EV landscape, probability distributions, and setup quality

## Integration Role
This analysis serves as the **PRIMARY ALGORITHM** in the analysis engine, with its recommendations taking priority over supplementary analyses. Risk analysis provides supporting context and confirmation signals.

---

## NQ Options Expected Value Trading System - Pseudocode
Based on the analysis logic applied to the provided options data

```pseudocode
PROGRAM NQ_Expected_Value_Trading_System

// ============================================================================
// CONSTANTS AND CONFIGURATION
// ============================================================================

CONSTANTS:
    WEIGHTS = {
        OI_FACTOR: 0.35,
        VOLUME_FACTOR: 0.25,
        PCR_FACTOR: 0.25,
        DISTANCE_FACTOR: 0.15
    }
    
    DISTANCE_WEIGHTS = {
        0.01: 1.0,    // 0-1% from current
        0.02: 0.8,    // 1-2% from current
        0.05: 0.5,    // 2-5% from current
        1.00: 0.2     // 5%+ from current
    }
    
    QUALITY_THRESHOLDS = {
        MIN_EV: 15,
        MIN_PROBABILITY: 0.60,
        MAX_RISK: 150,
        MIN_RISK_REWARD: 1.0
    }

// ============================================================================
// DATA STRUCTURES
// ============================================================================

STRUCTURE OptionsStrike:
    price: FLOAT
    call_volume: INTEGER
    call_oi: INTEGER
    call_premium: FLOAT
    put_volume: INTEGER
    put_oi: INTEGER
    put_premium: FLOAT
END STRUCTURE

STRUCTURE TradeSetup:
    target_price: FLOAT
    stop_loss: FLOAT
    direction: STRING  // "LONG" or "SHORT"
    probability: FLOAT
    reward: FLOAT
    risk: FLOAT
    expected_value: FLOAT
    risk_reward_ratio: FLOAT
    position_size: STRING
END STRUCTURE

// ============================================================================
// MAIN EXECUTION FUNCTION
// ============================================================================

FUNCTION main_trading_system():
    
    // Step 1: Load and parse options data
    options_data = load_options_data_from_barchart()
    current_price = estimate_current_price(options_data)
    
    // Step 2: Calculate market factors
    market_factors = calculate_market_factors(options_data, current_price)
    
    // Step 3: Generate all possible TP/SL combinations
    trade_combinations = generate_trade_combinations(current_price)
    
    // Step 4: Calculate EV for each combination
    evaluated_trades = []
    FOR each combination IN trade_combinations:
        probability = calculate_probability(current_price, combination, market_factors)
        ev_result = calculate_expected_value(combination, probability)
        evaluated_trades.append(ev_result)
    END FOR
    
    // Step 5: Filter and rank opportunities
    quality_trades = filter_quality_setups(evaluated_trades)
    ranked_trades = sort_by_expected_value(quality_trades)
    
    // Step 6: Check for perfect alignment
    perfect_setups = detect_perfect_alignment(ranked_trades, options_data)
    
    // Step 7: Generate recommendations
    recommendations = generate_trading_recommendations(ranked_trades, perfect_setups)
    
    RETURN recommendations
END FUNCTION

// ============================================================================
// DATA LOADING AND PREPROCESSING
// ============================================================================

FUNCTION load_options_data_from_barchart():
    // Parse the raw options chain data
    strikes = [21190, 21200, 21210, ..., 21350]
    
    options_data = []
    FOR each strike IN strikes:
        option_strike = OptionsStrike()
        option_strike.price = strike
        option_strike.call_volume = get_call_volume(strike)
        option_strike.call_oi = get_call_oi(strike)
        option_strike.call_premium = get_call_premium(strike)
        option_strike.put_volume = get_put_volume(strike)
        option_strike.put_oi = get_put_oi(strike)
        option_strike.put_premium = get_put_premium(strike)
        options_data.append(option_strike)
    END FOR
    
    RETURN options_data
END FUNCTION

FUNCTION estimate_current_price(options_data):
    // Find strikes with highest volume to estimate current price
    max_call_volume = 0
    max_put_volume = 0
    call_volume_strike = 0
    put_volume_strike = 0
    
    FOR each option IN options_data:
        IF option.call_volume > max_call_volume:
            max_call_volume = option.call_volume
            call_volume_strike = option.price
        END IF
        
        IF option.put_volume > max_put_volume:
            max_put_volume = option.put_volume
            put_volume_strike = option.price
        END IF
    END FOR
    
    // Current price is typically between high volume strikes
    estimated_price = (call_volume_strike + put_volume_strike) / 2
    RETURN estimated_price
END FUNCTION

// ============================================================================
// FACTOR CALCULATIONS
// ============================================================================

FUNCTION calculate_market_factors(options_data, current_price):
    market_factors = {}
    
    // Calculate Put/Call Ratio Factor
    total_call_premium = sum(option.call_premium FOR option IN options_data)
    total_put_premium = sum(option.put_premium FOR option IN options_data)
    
    market_factors.pcr_factor = (total_call_premium - total_put_premium) / 
                               (total_call_premium + total_put_premium)
    
    // Calculate maximum values for normalization
    max_oi = max(max(option.call_oi, option.put_oi) FOR option IN options_data)
    max_volume = max(max(option.call_volume, option.put_volume) FOR option IN options_data)
    
    market_factors.max_oi = max_oi
    market_factors.max_volume = max_volume
    market_factors.options_data = options_data
    
    RETURN market_factors
END FUNCTION

FUNCTION calculate_oi_factor(target_price, current_price, market_factors):
    oi_factor = 0
    
    FOR each option IN market_factors.options_data:
        distance_pct = abs(option.price - current_price) / current_price
        distance_weight = get_distance_weight(distance_pct)
        
        // Determine direction modifier
        IF target_price > current_price:  // Long trade
            direction_modifier = 1.0 IF option.price >= current_price ELSE -0.5
            weighted_oi = option.call_oi * distance_weight * direction_modifier
        ELSE:  // Short trade
            direction_modifier = 1.0 IF option.price <= current_price ELSE -0.5
            weighted_oi = option.put_oi * distance_weight * direction_modifier
        END IF
        
        oi_factor += weighted_oi
    END FOR
    
    // Normalize by maximum OI observed
    oi_factor = oi_factor / market_factors.max_oi
    RETURN clamp(oi_factor, 0, 1)
END FUNCTION

FUNCTION calculate_volume_factor(target_price, current_price, market_factors):
    volume_factor = 0
    
    FOR each option IN market_factors.options_data:
        distance_pct = abs(option.price - current_price) / current_price
        distance_weight = get_distance_weight(distance_pct)
        
        IF target_price > current_price:  // Long trade
            direction_modifier = 1.0 IF option.price >= current_price ELSE -0.5
            weighted_volume = option.call_volume * distance_weight * direction_modifier
        ELSE:  // Short trade
            direction_modifier = 1.0 IF option.price <= current_price ELSE -0.5
            weighted_volume = option.put_volume * distance_weight * direction_modifier
        END IF
        
        volume_factor += weighted_volume
    END FOR
    
    // Normalize by maximum volume observed
    volume_factor = volume_factor / market_factors.max_volume
    RETURN clamp(volume_factor, 0, 1)
END FUNCTION

FUNCTION calculate_distance_factor(current_price, target_price):
    distance_factor = 1 - (abs(current_price - target_price) / current_price)
    RETURN clamp(distance_factor, 0, 1)
END FUNCTION

FUNCTION get_distance_weight(distance_pct):
    IF distance_pct <= 0.01:
        RETURN 1.0
    ELSE IF distance_pct <= 0.02:
        RETURN 0.8
    ELSE IF distance_pct <= 0.05:
        RETURN 0.5
    ELSE:
        RETURN 0.2
    END IF
END FUNCTION

// ============================================================================
// PROBABILITY CALCULATION
// ============================================================================

FUNCTION calculate_probability(current_price, trade_combination, market_factors):
    target_price = trade_combination.target_price
    stop_loss = trade_combination.stop_loss
    direction = trade_combination.direction
    
    // Calculate individual factors
    oi_factor = calculate_oi_factor(target_price, current_price, market_factors)
    volume_factor = calculate_volume_factor(target_price, current_price, market_factors)
    pcr_factor = market_factors.pcr_factor
    distance_factor = calculate_distance_factor(current_price, target_price)
    
    // Apply weights and combine factors
    probability = (WEIGHTS.OI_FACTOR * oi_factor +
                  WEIGHTS.VOLUME_FACTOR * volume_factor +
                  WEIGHTS.PCR_FACTOR * pcr_factor +
                  WEIGHTS.DISTANCE_FACTOR * distance_factor)
    
    // Clamp probability between 10% and 90%
    probability = clamp(probability, 0.10, 0.90)
    
    RETURN probability
END FUNCTION

// ============================================================================
// EXPECTED VALUE CALCULATION
// ============================================================================

FUNCTION calculate_expected_value(trade_combination, probability):
    current_price = trade_combination.current_price
    target_price = trade_combination.target_price
    stop_loss = trade_combination.stop_loss
    direction = trade_combination.direction
    
    IF direction == "LONG":
        reward = target_price - current_price
        risk = current_price - stop_loss
    ELSE:  // SHORT
        reward = current_price - target_price
        risk = stop_loss - current_price
    END IF
    
    expected_value = (probability * reward) - ((1 - probability) * risk)
    risk_reward_ratio = reward / risk IF risk > 0 ELSE 0
    
    trade_setup = TradeSetup()
    trade_setup.target_price = target_price
    trade_setup.stop_loss = stop_loss
    trade_setup.direction = direction
    trade_setup.probability = probability
    trade_setup.reward = reward
    trade_setup.risk = risk
    trade_setup.expected_value = expected_value
    trade_setup.risk_reward_ratio = risk_reward_ratio
    
    RETURN trade_setup
END FUNCTION

// ============================================================================
// TRADE GENERATION AND FILTERING
// ============================================================================

FUNCTION generate_trade_combinations(current_price):
    combinations = []
    
    // Generate potential target prices (strikes within reasonable range)
    potential_targets = [current_price + i*10 FOR i IN range(-20, 21)]  // ±200 points
    potential_stops = [current_price + i*10 FOR i IN range(-20, 21)]
    
    FOR each target IN potential_targets:
        FOR each stop IN potential_stops:
            // Long trade: target > current > stop
            IF target > current_price AND stop < current_price:
                combination = {
                    current_price: current_price,
                    target_price: target,
                    stop_loss: stop,
                    direction: "LONG"
                }
                combinations.append(combination)
            END IF
            
            // Short trade: stop > current > target
            IF target < current_price AND stop > current_price:
                combination = {
                    current_price: current_price,
                    target_price: target,
                    stop_loss: stop,
                    direction: "SHORT"
                }
                combinations.append(combination)
            END IF
        END FOR
    END FOR
    
    RETURN combinations
END FUNCTION

FUNCTION filter_quality_setups(evaluated_trades):
    quality_setups = []
    
    FOR each trade IN evaluated_trades:
        IF (trade.expected_value >= QUALITY_THRESHOLDS.MIN_EV AND
            trade.probability >= QUALITY_THRESHOLDS.MIN_PROBABILITY AND
            trade.risk <= QUALITY_THRESHOLDS.MAX_RISK AND
            trade.risk_reward_ratio >= QUALITY_THRESHOLDS.MIN_RISK_REWARD):
            
            quality_setups.append(trade)
        END IF
    END FOR
    
    RETURN quality_setups
END FUNCTION

FUNCTION sort_by_expected_value(trades):
    // Sort trades in descending order by expected value
    RETURN sort(trades, key=lambda trade: trade.expected_value, reverse=True)
END FUNCTION

// ============================================================================
// PERFECT ALIGNMENT DETECTION
// ============================================================================

FUNCTION detect_perfect_alignment(ranked_trades, options_data):
    perfect_setups = []
    
    FOR each trade IN ranked_trades:
        target_strike = trade.target_price
        
        // Find if target matches high liquidity strike
        FOR each option IN options_data:
            IF option.price == target_strike:
                IF trade.direction == "LONG":
                    // Check for high call volume/OI at target
                    IF (option.call_volume > 100 OR option.call_oi > 50):
                        trade.perfect_alignment = True
                        perfect_setups.append(trade)
                    END IF
                ELSE:  // SHORT
                    // Check for high put volume/OI at target
                    IF (option.put_volume > 100 OR option.put_oi > 50):
                        trade.perfect_alignment = True
                        perfect_setups.append(trade)
                    END IF
                END IF
                BREAK
            END IF
        END FOR
    END FOR
    
    RETURN perfect_setups
END FUNCTION

// ============================================================================
// POSITION SIZING AND RECOMMENDATIONS
// ============================================================================

FUNCTION determine_position_size(expected_value):
    IF expected_value > 50:
        RETURN "LARGE (15-20% of portfolio)"
    ELSE IF expected_value > 30:
        RETURN "MEDIUM (10-15% of portfolio)"
    ELSE:
        RETURN "SMALL (5-10% of portfolio)"
    END IF
END FUNCTION

FUNCTION generate_trading_recommendations(ranked_trades, perfect_setups):
    recommendations = {
        top_opportunities: ranked_trades[0:5],  // Top 5 trades
        perfect_alignments: perfect_setups,
        primary_recommendation: null,
        secondary_recommendation: null
    }
    
    // Assign position sizes
    FOR each trade IN recommendations.top_opportunities:
        trade.position_size = determine_position_size(trade.expected_value)
    END FOR
    
    // Set primary recommendation (highest EV)
    IF len(ranked_trades) > 0:
        recommendations.primary_recommendation = ranked_trades[0]
    END IF
    
    // Set secondary recommendation (perfect alignment or second highest EV)
    IF len(perfect_setups) > 0:
        recommendations.secondary_recommendation = perfect_setups[0]
    ELSE IF len(ranked_trades) > 1:
        recommendations.secondary_recommendation = ranked_trades[1]
    END IF
    
    RETURN recommendations
END FUNCTION

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

FUNCTION clamp(value, min_val, max_val):
    RETURN max(min_val, min(value, max_val))
END FUNCTION

FUNCTION max(array):
    maximum = array[0]
    FOR each element IN array:
        IF element > maximum:
            maximum = element
        END IF
    END FOR
    RETURN maximum
END FUNCTION

FUNCTION sum(array):
    total = 0
    FOR each element IN array:
        total += element
    END FOR
    RETURN total
END FUNCTION

// ============================================================================
// MAIN PROGRAM EXECUTION
// ============================================================================

BEGIN MAIN:
    recommendations = main_trading_system()
    
    PRINT "=== NQ OPTIONS EXPECTED VALUE ANALYSIS ==="
    PRINT "Primary Recommendation:"
    PRINT recommendations.primary_recommendation
    
    PRINT "Top 5 Opportunities:"
    FOR each trade IN recommendations.top_opportunities:
        PRINT trade
    END FOR
    
    PRINT "Perfect Alignment Setups:"
    FOR each trade IN recommendations.perfect_alignments:
        PRINT trade
    END FOR
END MAIN

END PROGRAM
```