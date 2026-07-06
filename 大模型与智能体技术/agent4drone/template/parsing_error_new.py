"""
Parsing Error Template (Enhanced)

This template provides helpful error messages when the agent produces invalid JSON.
Includes guidance for formation control tasks.
"""

PARSING_ERROR_TEMPLATE = """Parsing error: {error}

ACTION INPUT MUST BE VALID JSON FORMAT:

✓ Correct Examples:
  - No parameters: {{}}
  - One parameter: {{"drone_id": "drone-001"}}
  - Multiple parameters: {{"drone_id": "drone-001", "altitude": 15.0, "x": 100.0, "y": 50.0, "z": 20.0}}

✗ Common Mistakes to Avoid:
  - Unmatched quotes: {{"drone_id": "drone-001}} ← Missing closing quote
  - Missing commas: {{"drone_id": "drone-001" "altitude": 15.0}} ← Need comma between parameters
  - Quotes around numbers: {{"altitude": "15.0"}} ← Numbers should NOT have quotes
  - Wrong bracket type: ["drone_id": "drone-001"] ← Use {{ }} not [ ]

FORMAT RULES:
- Use DOUBLE quotes for all strings and keys
- Use curly braces {{ }} for all JSON objects
- Separate multiple parameters with commas
- Numbers (integers and decimals) should NOT be quoted
- Boolean values should be lowercase: true or false
- Null values should be: null

FOR FORMATION CONTROL:
When working with drone positions, ensure:
- drone_id is a string: "drone-001"
- Coordinates are numbers: x: 100.0 (not "100.0")
- Altitude is a number: z: 20.0 (not "20.0")
- Distance values are numbers: 30.0 (not "30.0")

Please try again with proper JSON format.

Example for formation task:
Action Input: {{"drone_id": "drone-001", "x": 100.0, "y": 100.0, "z": 20.0}}
"""
