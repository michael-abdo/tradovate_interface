# Exception Handling Semantic Twins - Concrete Examples

## 1. Validation Pattern Twins (71 instances)

These are **exact semantic duplicates** - they all do the same thing with minor variations in the test name:

### Example Set A - From test_validation.py files
```python
# File: options_trading_system/output_generation/json_exporter/test_validation.py:84
except Exception as e:
    validation_results["tests"].append({
        "name": "exporter_init",
        "passed": False,
        "error": str(e)
    })
    print(f"   ✗ Error: {e}")
    return validation_results

# File: options_trading_system/output_generation/json_exporter/test_validation.py:132
except Exception as e:
    validation_results["tests"].append({
        "name": "data_serialization",
        "passed": False,
        "error": str(e)
    })
    print(f"   ✗ Error: {e}")

# File: options_trading_system/output_generation/json_exporter/test_validation.py:192
except Exception as e:
    validation_results["tests"].append({
        "name": "complete_json_export",
        "passed": False,
        "error": str(e)
    })
    print(f"   ✗ Error: {e}")
```

**Semantic Identity:** All three do EXACTLY the same thing:
1. Create a dict with name/passed/error
2. Append to validation_results["tests"]
3. Print error message
4. Sometimes return validation_results

**Could be replaced with:**
```python
add_validation_error(validation_results, "test_name", e)
```

## 2. Status Dict Pattern Twins (~15 instances)

### Example Set B - From integration.py files
```python
# File: options_trading_system/output_generation/integration.py:61
except Exception as e:
    print(f"    ✗ Trading Report failed: {str(e)}")
    return {
        "status": "failed",
        "error": str(e),
        "timestamp": get_utc_timestamp()
    }

# File: options_trading_system/output_generation/integration.py:96
except Exception as e:
    print(f"    ✗ JSON Export failed: {str(e)}")
    return {
        "status": "failed",
        "error": str(e),
        "timestamp": get_utc_timestamp()
    }

# File: options_trading_system/output_generation/integration.py:161
except Exception as e:
    print(f"    ✗ {output_type} generation failed: {str(e)}")
    self.generation_results[output_type] = {
        "status": "failed",
        "error": str(e),
        "timestamp": get_utc_timestamp()
    }
```

**Semantic Identity:** All return/set the same error structure:
- Always has status="failed"
- Always includes error message
- Always includes timestamp
- Only difference is the log message

**Could be replaced with:**
```python
return create_failure_response(e, "Trading Report")
```

## 3. Log and Return False Twins (20 instances)

### Example Set C - From validator files
```python
# File: options_trading_system/data_ingestion/barchart_web_scraper/expiration_validator.py:172
except Exception as e:
    self.logger.error(f"Error validating symbol {symbol}: {e}")
    return False

# File: options_trading_system/data_ingestion/barchart_web_scraper/symbol_generator.py:281
except Exception as e:
    self.logger.error(f"Validation error for {symbol}: {e}")
    return False

# File: options_trading_system/data_ingestion/barchart_web_scraper/hybrid_scraper.py:83
except Exception as e:
    self.logger.error(f"Failed to validate credentials: {e}")
    return False
```

**Semantic Identity:** All do exactly:
1. Log error with context
2. Return False

**Could use decorator:**
```python
@returns_false_on_error
def validate_symbol(self, symbol):
    # validation logic
```

## 4. Log and Return None Twins (5 instances)

### Example Set D - From data fetching
```python
# File: options_trading_system/data_ingestion/barchart_web_scraper/hybrid_scraper.py:120
except Exception as e:
    self.logger.error(f"API call failed: {e}")
    return None

# File: options_trading_system/data_ingestion/real_time_options_feed/solution.py:235
except Exception as e:
    logging.error(f"Error parsing options chain: {e}")
    return None

# File: options_trading_system/analysis_engine/volume_spike_dead_simple/baseline_data_manager.py:244
except Exception as e:
    logger.error(f"[BASELINE_MANAGER] Error calculating volume stats for {strike}{option_type[0]}: {e}")
    return None
```

**Semantic Identity:** Identical to False pattern but returns None

## Summary of True Semantic Duplicates

| Pattern | Count | Semantic Behavior | Consolidation Potential |
|---------|-------|-------------------|------------------------|
| Validation Dict Append | 71 | Append error dict to results | Single function |
| Status Failed Dict | ~15 | Return failure status dict | Single function |
| Log + Return False | 20 | Log and return False | Decorator |
| Log + Return None | 5 | Log and return None | Decorator |

**Total Semantic Twins: 111 out of 170 (65%)**

These 111 instances could be replaced with just 4 helper functions/decorators, eliminating ~800+ lines of duplicate error handling code.