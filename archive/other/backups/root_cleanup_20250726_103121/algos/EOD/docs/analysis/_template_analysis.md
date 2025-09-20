# [Analysis Name] ([Brief Descriptor])

## Philosophy & Meaning

The **[Analysis Name]** [brief description of what it does and why it's important]. This analysis [main purpose and what problem it solves].

### Core Philosophy
- **[Core Principle 1]**: [Explanation of the fundamental belief/approach]
- **[Core Principle 2]**: [Another key philosophical foundation]
- **[Core Principle 3]**: [Additional core concept]
- **[Core Principle 4]**: [Final foundational principle]

### [Key Concepts/Factors/Methods] ([Custom Section Name])
1. **[Concept 1] ([Weight/Importance])** - [Detailed explanation of this concept]
2. **[Concept 2] ([Weight/Importance])** - [Detailed explanation of this concept]
3. **[Concept 3] ([Weight/Importance])** - [Detailed explanation of this concept]
4. **[Concept 4] ([Weight/Importance])** - [Detailed explanation of this concept]

### [Analysis-Specific Section] (Optional)
- **[Specific Parameter 1]**: [Value/Description]
- **[Specific Parameter 2]**: [Value/Description]
- **[Specific Parameter 3]**: [Value/Description]
- **[Specific Parameter 4]**: [Value/Description]

### [Trading/Market Implications] (Optional but Recommended)
- **[Scenario 1]**: [What this means for trading and market behavior]
- **[Scenario 2]**: [Another scenario and its implications]
- **[Scenario 3]**: [Additional scenario description]
- **[Pattern Recognition]**: [How patterns are identified and used]

## Trading Signals Generated
- **[SIGNAL TYPE 1]**: [Description of primary output/recommendation type]
- **[SIGNAL TYPE 2]**: [Description of secondary output type]
- **[SIGNAL TYPE 3]**: [Description of additional metrics/data provided]
- **[SIGNAL TYPE 4]**: [Description of supporting analysis elements]

## Integration Role
This analysis [describe how it fits in the broader system - is it primary, supplementary, confirmatory?] by [explaining its specific contribution]. [Describe how it interacts with other analyses and where it fits in the decision-making hierarchy].

---

## [Analysis Name] - Pseudocode
[Brief description of what the pseudocode represents]

```pseudocode
PROGRAM [Analysis_Name]_System

// ============================================================================
// CONSTANTS AND CONFIGURATION
// ============================================================================

CONSTANTS:
    [CONSTANT_GROUP_1] = {
        [PARAM_1]: [value],    // [Comment explaining purpose]
        [PARAM_2]: [value],    // [Comment explaining purpose]
        [PARAM_3]: [value],    // [Comment explaining purpose]
        [PARAM_4]: [value]     // [Comment explaining purpose]
    }
    
    [CONSTANT_GROUP_2] = {
        [THRESHOLD_1]: [value],     // [Comment on when/how used]
        [THRESHOLD_2]: [value],     // [Comment on significance]
        [THRESHOLD_3]: [value],     // [Comment on application]
        [THRESHOLD_4]: [value]      // [Comment on meaning]
    }
    
    [CATEGORIES/CLASSIFICATIONS] = {
        [CATEGORY_1]: [value],    // [Description of this category]
        [CATEGORY_2]: [value],    // [Description of this category]
        [CATEGORY_3]: [value],    // [Description of this category]
        [CATEGORY_4]: [value]     // [Description of this category]
    }

// ============================================================================
// DATA STRUCTURES
// ============================================================================

STRUCTURE [PrimaryDataStructure]:
    [field_1]: [TYPE]        // [Description of what this represents]
    [field_2]: [TYPE]        // [Description of what this represents]
    [field_3]: [TYPE]        // [Description of what this represents]
    [field_4]: [TYPE]        // [Description of what this represents]
    [field_5]: [TYPE]        // [Description of what this represents]
END STRUCTURE

STRUCTURE [SecondaryDataStructure]:
    [field_1]: [TYPE]          // [Description]
    [field_2]: [TYPE]          // [Description]
    [field_3]: [TYPE]          // [Description]
    [field_4]: [TYPE]          // [Description]
END STRUCTURE

STRUCTURE [ResultDataStructure]:
    [result_field_1]: [TYPE]
    [result_field_2]: [TYPE]
    [result_field_3]: [TYPE]
    [result_field_4]: [TYPE]
    [result_field_5]: ARRAY[[SubStructure]]
    [result_field_6]: ARRAY[[SubStructure]]
END STRUCTURE

// ============================================================================
// MAIN ANALYSIS FUNCTION
// ============================================================================

FUNCTION [main_analysis_function](input_data, parameters):
    // Step 1: [Description of first major step]
    [step1_result] = [function_call](input_data)
    
    // Step 2: [Description of second major step]
    [step2_result] = [function_call]([step1_result], parameters)
    
    // Step 3: [Description of third major step]
    [step3_result] = [function_call]([step1_result], [step2_result])
    
    // Step 4: [Description of fourth major step]
    [step4_result] = [function_call]([step3_result], parameters)
    
    // Step 5: [Description of fifth major step]
    [step5_result] = [function_call]([step4_result])
    
    // Step 6: [Description of sixth major step]
    [step6_result] = [function_call]([multiple_inputs])
    
    // Step 7: [Final compilation/result generation]
    final_result = [ResultDataStructure]()
    [populate_final_result_fields]
    
    RETURN final_result
END FUNCTION

// ============================================================================
// [CATEGORY 1] FUNCTIONS
// ============================================================================

FUNCTION [category1_function_1]([parameters]):
    [detailed_implementation_logic]
    
    FOR each [item] IN [collection]:
        [processing_logic]
        
        IF [condition]:
            [action]
        ELSE IF [condition]:
            [alternative_action]
        ELSE:
            [default_action]
        END IF
        
        [additional_processing]
    END FOR
    
    RETURN [result]
END FUNCTION

FUNCTION [category1_function_2]([parameters]):
    [implementation_details]
    RETURN [result]
END FUNCTION

// ============================================================================
// [CATEGORY 2] FUNCTIONS
// ============================================================================

FUNCTION [category2_function_1]([parameters]):
    [detailed_logic]
    RETURN [result]
END FUNCTION

FUNCTION [category2_function_2]([parameters]):
    [implementation]
    
    // [Step-by-step breakdown with comments]
    [calculation_logic]
    
    // [Normalization or adjustment logic]
    [adjustment_logic]
    
    RETURN [final_calculation]
END FUNCTION

// ============================================================================
// [CATEGORY 3] FUNCTIONS
// ============================================================================

FUNCTION [category3_function_1]([parameters]):
    [analysis_logic]
    
    // [Pattern recognition or classification logic]
    IF [pattern_condition_1]:
        [action_1]
    ELSE IF [pattern_condition_2]:
        [action_2]
    END IF
    
    RETURN [analysis_result]
END FUNCTION

// ============================================================================
// [DECISION/VERDICT] GENERATION
// ============================================================================

FUNCTION [decision_function]([analysis_results]):
    [decision_logic]
    
    // [Classification based on results]
    IF [result] >= [THRESHOLD_1]:
        [classification] = "[HIGH_CATEGORY]"
        [description] = "[Detailed explanation]"
    ELSE IF [result] >= [THRESHOLD_2]:
        [classification] = "[MEDIUM_CATEGORY]"
        [description] = "[Detailed explanation]"
    ELSE:
        [classification] = "[LOW_CATEGORY]"
        [description] = "[Detailed explanation]"
    END IF
    
    // [Additional context or adjustments]
    IF [special_condition]:
        [description] += " | [Additional context]"
    END IF
    
    RETURN {
        [field1]: [classification],
        [field2]: [description]
    }
END FUNCTION

// ============================================================================
// [SIGNAL/OUTPUT] GENERATION
// ============================================================================

FUNCTION [signal_generation_function]([analysis_results]):
    signals = []
    
    // Signal 1: [Primary signal description]
    signals.append("[SIGNAL_TYPE]: " + [primary_result])
    
    // Signal 2: [Secondary signal description]
    IF [condition]:
        signals.append("[SIGNAL_DESCRIPTION]: " + [specific_result])
    END IF
    
    // Signal 3: [Pattern-based signals]
    FOR [pattern] IN [identified_patterns]:
        IF [pattern] == "[PATTERN_TYPE_1]":
            signals.append("[SPECIFIC_SIGNAL_1]")
        ELSE IF [pattern] == "[PATTERN_TYPE_2]":
            signals.append("[SPECIFIC_SIGNAL_2]")
        END IF
    END FOR
    
    // Signal 4: [Threshold-based alerts]
    IF [critical_condition]:
        signals.append("[ALERT_TYPE]: " + [details])
    END IF
    
    RETURN signals
END FUNCTION

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

FUNCTION [utility_function_1]([parameters]):
    [basic_utility_implementation]
    RETURN [result]
END FUNCTION

FUNCTION [utility_function_2]([parameters]):
    [another_utility_implementation]
    RETURN [result]
END FUNCTION

FUNCTION [utility_function_3]([parameters]):
    [complex_utility_with_logic]
    RETURN [result]
END FUNCTION

// ============================================================================
// MAIN PROGRAM EXECUTION
// ============================================================================

BEGIN MAIN:
    // Load input data
    [input_data] = [load_data_function]()
    [parameters] = [get_parameters]()
    
    // Run analysis
    [analysis_result] = [main_analysis_function]([input_data], [parameters])
    
    // Display results
    PRINT "=== [ANALYSIS NAME HEADER] ==="
    PRINT "[Context Information]: " + [relevant_data]
    PRINT ""
    PRINT "[PRIMARY RESULTS SECTION]:"
    PRINT "  [Result 1]: " + [format_function]([analysis_result].[field1])
    PRINT "  [Result 2]: " + [format_function]([analysis_result].[field2])
    PRINT "  [Result 3]: " + [format_function]([analysis_result].[field3])
    PRINT ""
    PRINT "[VERDICT/CONCLUSION]: " + [analysis_result].[verdict]
    PRINT "[BIAS/DIRECTION]: " + [analysis_result].[bias]
    PRINT ""
    PRINT "[DETAILED BREAKDOWN SECTION]:"
    FOR each [item] IN [analysis_result].[detailed_items]:
        PRINT "  [Item]: " + [format_details]([item])
    END FOR
    PRINT ""
    PRINT "[KEY SIGNALS/ACTIONABLES]:"
    FOR each [signal] IN [analysis_result].[signals]:
        PRINT "  • " + [signal]
    END FOR
END MAIN

END PROGRAM
```

---

## Template Usage Instructions

### Required Sections (Must Include):
1. **Title**: Clear, descriptive name with brief descriptor
2. **Philosophy & Meaning**: The "why" - purpose and theoretical foundation
3. **Core Philosophy**: 3-4 bullet points of fundamental principles
4. **Key Concepts**: Numbered list of main components (factors, methods, etc.)
5. **Trading Signals Generated**: What outputs this analysis produces
6. **Integration Role**: How it fits in the broader system
7. **Pseudocode**: Complete implementation logic

### Optional Sections (Include When Relevant):
- **Analysis-Specific Parameters**: Thresholds, weights, configurations
- **Trading/Market Implications**: Scenarios and their meanings
- **Quality Criteria**: Standards for filtering or ranking results
- **Pattern Recognition**: How patterns are identified and used

### Pseudocode Structure Guidelines:
1. **Constants**: All configurable parameters with clear comments
2. **Data Structures**: Clear field definitions with purpose comments
3. **Main Function**: Step-by-step breakdown of the analysis flow
4. **Supporting Functions**: Grouped by logical categories
5. **Utility Functions**: Helper functions for common operations
6. **Main Execution**: Example of how results are displayed

### Documentation Standards:
- Each section should be comprehensive enough for someone to understand the analysis without external references
- Include specific examples, thresholds, and decision criteria
- Explain both the technical implementation AND the trading rationale
- Provide clear linkage between philosophy and implementation
- Include expected outputs and how they should be interpreted