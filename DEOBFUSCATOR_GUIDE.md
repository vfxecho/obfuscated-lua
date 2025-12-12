# Luraph v14 Deobfuscator Guide

## Overview

This project contains tools for analyzing and deobfuscating Lua scripts protected by **Luraph Obfuscator v14.x**. The deobfuscator is designed to extract bytecode, analyze the virtual machine structure, and reconstruct the original code.

## What is Luraph v14?

Luraph is a commercial Lua obfuscator that:
- Compiles Lua source code into a custom bytecode format
- Embeds a self-contained virtual machine to execute the bytecode
- Uses multiple obfuscation techniques to hide the original code
- Protects intellectual property by making reverse engineering difficult

### Obfuscation Techniques Used

1. **Control Flow Flattening (CFF)**
   - Complex decision trees instead of simple switch statements
   - Binary tree structure for opcode dispatch
   - State machines with non-obvious transitions

2. **Structure of Arrays (SoA)**
   - Instruction data split across multiple arrays (e, u, Y, L, H)
   - Instead of traditional Array of Structs format
   - Makes bytecode format unrecognizable to standard decompilers

3. **Variable Renaming**
   - All variables reduced to single letters or garbage names
   - Variable reuse and recycling
   - Meaningless identifiers

4. **Mixed Radix Literals**
   - Hex (0x...) and binary (0b...) numbers mixed
   - Numbers split with underscores (0B10__1001__1)
   - Makes regex-based searching difficult

5. **String Encryption**
   - Constant strings packed and encrypted
   - Runtime decryption using bit32 operations
   - Custom encoding schemes

6. **Dead Code & Junk Instructions**
   - Unreachable branches in control flow
   - Redundant calculations
   - Confuses static analyzers

## Project Structure

### Tools Included

#### 1. `luraph_deobfuscator.py` - Main Analysis Tool
The primary deobfuscator written in Python.

**Features:**
- Script structure analysis
- Function identification
- Obfuscation technique detection
- VM architecture analysis
- Bytecode pattern recognition
- Comprehensive reporting

**Usage:**
```bash
python3 luraph_deobfuscator.py over.lua
```

**Output:**
- Console analysis report
- ANALYSIS_REPORT.txt - Detailed findings

#### 2. `deobfuscator.lua` - Lua Analysis Module
Lua-based analysis tool for deeper inspection.

**Features:**
- Lua-native pattern matching
- Hex dump utilities
- Bytecode extraction helpers
- VM structure analysis

**Usage:**
```bash
lua deobfuscator.lua
```

#### 3. `vm_dumper.lua` - VM State Dumper
Attempts to hook into the VM during execution.

**Features:**
- VM execution tracing
- State capture
- Function identification
- Bytecode dumping

**Usage:**
```bash
lua vm_dumper.lua
```

#### 4. `bytecode_extractor.lua` - Bytecode Extractor
Extracts instruction streams and constants.

**Features:**
- Bytecode header generation
- Instruction array extraction
- Constant table dumping
- Disassembly output

**Usage:**
```bash
lua bytecode_extractor.lua
```

## Deobfuscation Process

### Stage 1: Analysis
```bash
python3 luraph_deobfuscator.py over.lua
```

This stage:
1. Loads the obfuscated script
2. Analyzes its structure
3. Identifies obfuscation techniques
4. Finds key VM functions
5. Generates analysis report

### Stage 2: VM Investigation
```bash
lua bytecode_extractor.lua
```

This stage:
1. Loads the script in a Lua environment
2. Attempts to capture the VM state
3. Extracts instruction arrays
4. Dumps constants and data

### Stage 3: Bytecode Reconstruction
(Would require custom Lua interpreter modifications)

To fully extract bytecode, you would need to:

1. **Modify the Lua interpreter** to add debugging hooks
2. **Hook into the VM execution** to capture:
   - Instruction arrays (e, u, Y, L)
   - Constants table (H)
   - Function prototypes
   - Upvalues and environments

3. **Reconstruct Lua 5.1 bytecode** format
4. **Generate .luac file** (binary Lua bytecode)

### Stage 4: Decompilation
(Requires Stage 3 to be complete)

```bash
unluac output.luac > output.lua
```

## VM Architecture

### Main Components

#### Instruction Format (Structure of Arrays)

Instead of standard format:
```lua
-- Standard: Array of Structs
instruction = {
    opcode = 11,   -- ADD opcode
    A = 0,         -- Register A
    B = 1,         -- Register B  
    C = 2,         -- Register C
}
```

Luraph v14 uses:
```lua
-- SoA Format: Structure of Arrays
e[1] = 11       -- Opcodes array
u[1] = 0        -- Operand A array
Y[1] = 1        -- Operand B array
L[1] = 2        -- Operand C array
H[1] = const    -- Constants array
```

#### Main Execution Loop

```lua
repeat
    local d = e[Q]  -- Fetch opcode
    
    -- Binary decision tree dispatch
    if not(d < 55) then
        if d < 75 then
            -- Handle opcodes 55-74
        else
            -- Handle opcodes 75+
        end
    else
        -- Handle opcodes 0-54
    end
    
    Q += 1  -- Increment program counter
until false
```

#### Key Variables

| Variable | Purpose |
|----------|---------|
| Q | Program Counter / Instruction Pointer |
| Z | Registers / Stack (local table) |
| k | Stack Pointer / Top of Stack |
| e[] | Opcode array |
| u[] | Operand A array |
| Y[] | Operand B array |
| L[] | Operand C array |
| H[] | Constants array |

### Opcode Dispatch

The dispatch uses nested if-else blocks instead of a lookup table:

```lua
-- Pattern: Binary decision tree
if d < 55 then
    if d < 28 then
        if d < 14 then
            -- Opcodes 0-13
        else
            -- Opcodes 14-27
        end
    else
        -- Opcodes 28-54
    end
else
    -- Opcodes 55+
end
```

This makes it hard to identify opcodes without:
1. Tracing execution
2. Analyzing the decision tree
3. Pattern matching against Lua 5.1 opcodes

## Analysis Findings

### Key Functions Identified

- **`ty`**: VM initialization function
  - Sets up the VM state
  - Loads instruction streams
  - Configures opcode handlers
  - Manages execution

- **`Ly`**: Bytecode loader
  - Parses encrypted bytecode
  - Splits into SoA format
  - Initializes constants

- **`Ck`**: Main execution loop
  - Implements the repeat-until VM loop
  - Dispatches opcodes
  - Manages registers and stack

- **`Uk`**: Utility function
  - State machine with heavy CFF
  - Likely handles decryption or validation

### Bytecode Characteristics

- **Format**: Structure of Arrays (SoA)
- **Instruction Size**: Variable (split across arrays)
- **Encoding**: Likely encrypted or compressed
- **Constants**: Encrypted at rest, decrypted at runtime
- **String Pool**: Custom packing format

## Reverse Engineering Challenges

1. **No Direct Bytecode Access**
   - Need to hook VM execution at runtime
   - Standard debugging won't work easily

2. **Dynamic Code Generation**
   - Some code may be generated at runtime
   - Prototypes modified during execution

3. **Anti-Tampering**
   - May detect modifications
   - Could implement code integrity checks

4. **Encryption**
   - Unknown key derivation
   - Custom cipher or format

## Advanced Techniques

### Dynamic Execution Hooking

To extract bytecode at runtime:

```lua
-- Hook into debug library
debug.sethook(function(event)
    if event == "line" then
        -- Capture VM state
        local info = debug.getinfo(2)
        if info.name == "Ck" or info.name == "ty" then
            -- Extract instruction arrays
        end
    end
end, "l")

-- Execute the obfuscated script
dofile("over.lua")
```

### Pattern-Based Opcode Mapping

Analyze the decision tree to map operations:

```python
# Extract opcode dispatch tree
dispatch_pattern = re.findall(r'if\s+not\(d\s*<\s*(\d+)\)', content)

# Build decision tree
tree = build_decision_tree(dispatch_pattern)

# Match against known patterns
for opcode_name, pattern in lua_opcode_patterns.items():
    if matches_pattern(tree[opcode], pattern):
        opcode_map[opcode] = opcode_name
```

### SoA to Bytecode Conversion

Convert Structure of Arrays back to standard format:

```python
def convert_soa_to_bytecode(e, u, Y, L, H):
    """Convert SoA instruction format to standard bytecode"""
    instructions = []
    
    for i in range(len(e)):
        opcode = e[i]
        arg_a = u[i] if i < len(u) else 0
        arg_b = Y[i] if i < len(Y) else 0
        arg_c = L[i] if i < len(L) else 0
        
        # Reconstruct standard instruction word
        instruction = opcode | (arg_a << 6) | (arg_b << 14) | (arg_c << 23)
        instructions.append(instruction)
    
    return instructions
```

## Expected Results

### Analysis Report Output

The analysis tool generates:

1. **Script Metadata**
   - File size and line count
   - Function count and definitions
   - VM initialization markers

2. **Structure Analysis**
   - Identified obfuscation techniques
   - SoA format confirmation
   - Control flow flattening patterns

3. **Function Map**
   - Key functions identified
   - Function boundaries
   - Call relationships

4. **Bytecode Characteristics**
   - Instruction array locations
   - Constants table structure
   - Encoded data patterns

5. **Deobfuscation Recommendations**
   - Dynamic hooking approaches
   - Pattern-based extraction
   - Tool usage guidelines

## Limitations

1. **Static Analysis Only**
   - Current tools perform static analysis
   - Cannot directly execute or hook the VM
   - Would require modified Lua interpreter

2. **Encrypted Bytecode**
   - If bytecode is encrypted, key must be recovered
   - May be key-based or hardware-based

3. **Anti-Tampering Checks**
   - Script may verify its own integrity
   - May prevent extraction attempts

4. **Version-Specific**
   - These tools are specific to Luraph v14.x
   - Other versions may use different techniques

## Future Improvements

1. **Dynamic Interpreter Hooks**
   - Create modified Lua 5.1 with debug hooks
   - Capture VM state during execution
   - Extract bytecode automatically

2. **Opcode Pattern Database**
   - Build comprehensive pattern library
   - Automatic opcode identification
   - Confidence scoring

3. **Bytecode Reconstructor**
   - Automatic Lua 5.1 bytecode generation
   - Function prototype building
   - .luac file generation

4. **Integration with Decompilers**
   - Direct Unluac integration
   - Source code reconstruction
   - Variable/function renaming hints

## References

- [Lua 5.1 Official Documentation](https://www.lua.org/manual/5.1/)
- [Lua 5.1 Bytecode Format](https://en.wikipedia.org/wiki/Lua_(programming_language)#Bytecode)
- [Unluac Decompiler](https://sourceforge.net/projects/unluac/)
- [Luraph Official](https://lura.ph/)

## Contributing

To improve this deobfuscator:

1. Add support for other Luraph versions
2. Implement dynamic execution hooks
3. Create comprehensive opcode pattern database
4. Build bytecode reconstruction pipeline
5. Integrate with existing decompilers

## License

This deobfuscator is provided for educational and research purposes only.

## Disclaimer

Deobfuscating scripts may violate license agreements or intellectual property rights. Always ensure you have proper authorization before attempting to deobfuscate code.

---

**Last Updated**: 2024
**Status**: Analysis and Documentation Complete
**Next Phase**: Dynamic Extraction Tools
