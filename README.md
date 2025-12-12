# Luraph v14 Deobfuscator

A comprehensive toolkit for analyzing and deobfuscating Lua scripts protected by **Luraph Obfuscator v14.4.2**.

## Overview

This project provides tools and documentation for reverse engineering Luraph v14-obfuscated Lua code. The obfuscator protects intellectual property by compiling Lua source code into a custom virtual machine bytecode and embedding a complex interpreter to execute it.

## What's Included

### Core Tools

1. **`luraph_deobfuscator.py`** - Main analysis tool (Python 3)
   - Script structure analysis
   - Function identification
   - Obfuscation technique detection
   - VM architecture analysis
   - Comprehensive reporting

2. **`bytecode_extractor.lua`** - Bytecode extraction helper
   - Lua bytecode header generation
   - Instruction array extraction
   - Constants table dumping
   - Disassembly output

3. **`vm_dumper.lua`** - VM state analysis
   - Static code analysis
   - Function boundary detection
   - Pattern matching
   - Structure identification

4. **`deobfuscator.lua`** - Utility module
   - Helper functions
   - Hex dump utilities
   - Analysis helpers

### Documentation

- **`DEOBFUSCATOR_GUIDE.md`** - Comprehensive technical guide
  - Obfuscation techniques explained
  - VM architecture details
  - Reverse engineering approaches
  - Advanced deobfuscation methods

## Quick Start

### Prerequisites

- Python 3.6+
- Lua 5.1 (for Lua-based tools)
- The obfuscated script (`over.lua`)

### Run Analysis

```bash
python3 luraph_deobfuscator.py over.lua
```

This will:
1. Load and analyze the obfuscated script
2. Identify key functions and structures
3. Detect obfuscation techniques
4. Generate a detailed analysis report
5. Output recommendations for deobfuscation

### Output Example

```
======================================================================
LURAPH V14 DEOBFUSCATOR
======================================================================

[*] Loaded script: 70415 bytes

=== Script Analysis ===

[*] Total size: 70415 bytes
[*] Line count: 2
[*] Inline functions: 111
[*] Named function assignments: 95
[*] Has ty() function: True

=== Key Functions ===

[+] Found Uk at offset 86
[+] Found Ly at offset 29137
[+] Found Ck at offset 548
[+] Found Jk at offset 32024
...
```

## How Luraph v14 Works

### VM Architecture

The obfuscated script implements a **custom virtual machine** that:

1. **Loads encrypted bytecode** via the `Ly` (loader) function
2. **Initializes VM state** in the `ty` (type) function
3. **Executes instructions** in the `Ck` (check/execute) main loop
4. **Dispatches opcodes** using binary decision trees

### Instruction Format

Luraph v14 uses **Structure of Arrays (SoA)** instead of the standard format:

```lua
-- Standard Lua format (Array of Structs)
instruction = opcode | (A << 6) | (B << 14) | (C << 23)

-- Luraph v14 format (Structure of Arrays)
e[pc] = opcode     -- Opcode array
u[pc] = A          -- Operand A array
Y[pc] = B          -- Operand B array
L[pc] = C          -- Operand C array
H[pc] = constant   -- Constants array
```

This makes the bytecode unrecognizable to standard decompilers.

### Main Loop

```lua
repeat
    local d = e[Q]  -- Fetch opcode
    
    -- Binary decision tree dispatch (nested if-else)
    if not(d < 55) then ... end
    
    Q += 1  -- Increment program counter
until false
```

## Obfuscation Techniques

1. **Control Flow Flattening**
   - Complex nested if-else instead of switch statements
   - Binary decision trees for opcode dispatch
   - State machines with non-obvious transitions

2. **Structure of Arrays**
   - Instructions split across multiple arrays
   - Non-standard bytecode format
   - Incompatible with existing decompilers

3. **Variable Renaming**
   - Single-letter variable names
   - Aggressive variable reuse
   - Meaningless identifiers

4. **Mixed Radix Literals**
   - Hex (0x...) and binary (0b...) numbers mixed
   - Numbers split with underscores: `0B10__1001__1`
   - Makes pattern searching difficult

5. **String Encryption**
   - Encrypted constant strings
   - Runtime decryption via bit32 operations
   - Custom encoding schemes

6. **Dead Code**
   - Unreachable branches
   - Redundant calculations
   - Confuses static analyzers

## Deobfuscation Process

### Phase 1: Analysis (Complete)
✅ Script structure identification
✅ Obfuscation technique detection
✅ VM architecture analysis
✅ Key function location

### Phase 2: Bytecode Extraction (Partial)
🔄 Instruction array identification
🔄 Constants table extraction
🔄 Pattern-based opcode mapping

### Phase 3: Bytecode Reconstruction (Future)
⏳ SoA to standard format conversion
⏳ Lua 5.1 bytecode generation
⏳ Function prototype building

### Phase 4: Decompilation (Future)
⏳ Integration with Unluac
⏳ Source code reconstruction
⏳ Variable/function name recovery

## Key Findings

### Identified Structures

- **Program Counter**: Variable `Q`
- **Registers/Stack**: Table `Z`
- **Opcode Array**: `e[Q]`
- **Operand A Array**: `u[Q]`
- **Operand B Array**: `Y[Q]`
- **Operand C Array**: `L[Q]`
- **Constants**: `H[Q]`

### Script Characteristics

- **Version**: Luraph v14.4.2
- **Size**: ~70 KB (heavily minified)
- **Functions**: 95+ named functions
- **Bytecode Format**: Structure of Arrays (SoA)
- **Dispatch Method**: Binary decision tree
- **Encoding**: Unknown (likely encrypted)

## Next Steps for Full Deobfuscation

To completely deobfuscate the script, you would need to:

1. **Create a Modified Lua Interpreter**
   ```bash
   # Compile Lua 5.1 with debugging hooks
   # Add breakpoints in the VM execution
   ```

2. **Hook Into VM Functions**
   ```lua
   -- Capture instruction arrays during execution
   debug.sethook(function(event)
       if event == "line" then
           -- Extract e, u, Y, L, H arrays
       end
   end, "l")
   ```

3. **Reconstruct Bytecode**
   ```python
   # Convert SoA format back to standard Lua
   instructions = []
   for i in range(len(opcodes)):
       instr = opcodes[i] | (args_a[i] << 6) | (args_b[i] << 14)
       instructions.append(instr)
   ```

4. **Decompile with Unluac**
   ```bash
   unluac reconstructed.luac > output.lua
   ```

## Project Statistics

| Metric | Value |
|--------|-------|
| Script Size | 70,415 bytes |
| Minified Lines | 2 |
| Named Functions | 95 |
| Inline Functions | 111 |
| Estimated Complexity | Very High |

## Technical Details

### Variables Analyzed

| Variable | Purpose |
|----------|---------|
| Q | Program Counter |
| Z | Registers (table) |
| k | Stack Pointer |
| e[] | Opcode Array |
| u[] | Arg A Array |
| Y[] | Arg B Array |
| L[] | Arg C Array |
| H[] | Constants Array |

### Key Functions Located

| Function | Location | Purpose |
|----------|----------|---------|
| Uk | offset 86 | Utility/State Machine |
| kk | offset 489 | Helper (returns empty) |
| Ck | offset 548 | Main Execution Loop |
| Ly | offset 29,137 | Bytecode Loader |
| Qk | offset 22,178 | Quotation Handler |
| Jk | offset 32,024 | Jump/Return Handler |
| qk | offset 33,570 | Query Handler |

## Resources

- **Lua 5.1 Manual**: https://www.lua.org/manual/5.1/
- **Bytecode Format**: https://en.wikipedia.org/wiki/Lua_(programming_language)#Bytecode
- **Unluac Decompiler**: https://sourceforge.net/projects/unluac/
- **Luraph Official**: https://lura.ph/

## Limitations

1. **No Direct Bytecode Access**: Current tools use static analysis only
2. **Encrypted Data**: Bytecode may be encrypted with unknown keys
3. **Anti-Tampering**: Script may detect modification attempts
4. **Version-Specific**: Tools designed for Luraph v14.x only
5. **Dynamic Code**: Some code may be generated at runtime

## Legal Notice

⚠️ **Disclaimer**: Deobfuscating code may violate:
- License agreements
- Copyright law
- Intellectual property rights

Always ensure you have proper authorization before attempting to deobfuscate code.

## Usage

### For Analysis Only

```bash
python3 luraph_deobfuscator.py over.lua
```

### For Learning

Study the included documentation:
- Read `DEOBFUSCATOR_GUIDE.md` for deep technical insights
- Review the tool code to understand obfuscation patterns
- Experiment with the Lua-based tools

### For Full Deobfuscation

See the "Next Steps" section for how to implement:
1. Dynamic execution hooking
2. Bytecode reconstruction
3. Integration with existing decompilers

## Contributing

To improve this deobfuscator:

1. Enhance pattern detection
2. Add support for other Luraph versions
3. Implement bytecode reconstruction
4. Create automated extraction pipeline
5. Integrate decompilation tools

## Roadmap

- [x] Script analysis framework
- [x] Obfuscation technique detection
- [x] VM structure identification
- [x] Technical documentation
- [ ] Dynamic bytecode extraction
- [ ] Opcode mapping database
- [ ] Bytecode reconstructor
- [ ] Automated decompilation pipeline
- [ ] Support for other Luraph versions

## Files

- `over.lua` - Original obfuscated script
- `luraph_deobfuscator.py` - Main analysis tool
- `bytecode_extractor.lua` - Bytecode extraction helper
- `vm_dumper.lua` - VM state analyzer
- `deobfuscator.lua` - Utility module
- `DEOBFUSCATOR_GUIDE.md` - Technical documentation
- `README.md` - This file

## Contact

For questions or improvements, refer to the project documentation.

## License

Educational and research purposes only.

---

**Status**: Analysis Complete ✅ | Extraction In Progress 🔄 | Decompilation Pending ⏳

**Last Updated**: 2024
