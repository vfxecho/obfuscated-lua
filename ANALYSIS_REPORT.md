# Luraph v14 Obfuscation Analysis Report

## Overview
The provided file `over.lua` is a Lua 5.1 script protected by **Luraph Obfuscator v14.x** (specifically identifying itself as v14.4.2 in the header). The script functions as a self-contained custom Virtual Machine (VM) designed to load, decrypt, and execute a bundled bytecode payload. The entire logic is encapsulated within a large table returned by an anonymous function, which is immediately executed via the `:ty()` method.

## VM Architecture

### 1. Main Loop & Execution Flow
The VM's execution core is located within the `Ck` function (key `Ck` in the main table).
*   **Instruction Pointer:** The variable `Q` serves as the Program Counter (PC).
*   **Main Loop:** A `repeat ... until false` loop iterates through instructions.
    ```lua
    repeat
        local d = (e[Q]); -- Fetch Opcode
        -- Dispatch Logic (Binary Search Tree)
        if not(d < 0B110111) then ... end
        -- ...
        Q += 1; -- Increment PC
    until false;
    ```

### 2. Instruction Format (Structure of Arrays)
Unlike standard Lua which uses an Array of Structs (instruction words), this VM utilizes a **Structure of Arrays (SoA)** layout to store instructions. This is a known performance optimization and obfuscation technique in Luraph v14.
*   `e`: Array of **Opcodes** (Instruction IDs).
*   `u`: Array of **Operand A**.
*   `Y`: Array of **Operand B**.
*   `L`: Array of **Operand C**.
*   `H`: Array of **Constants** (or K).

Instead of decoding an instruction integer at runtime (e.g., `OP = Inst & 0x3F`), the loader pre-splits the bytecode into these parallel arrays (`e`, `u`, `Y`, `L`) during the initialization phase (handled by function `Ly`).

### 3. Registers & Stack
*   **Registers (`Z`):** A local table `Z` acts as the VM's register file and stack.
*   **Stack Pointer:** The variable `k` is used to track the top of the stack.
*   **Constants:** Stored in table `H` (loaded from `I[0b1010]`).
*   **Upvalues/Environment:** Handled via the variable `a` and `i` tables.

## Opcode Dispatch Logic
The opcode dispatcher does not use a clean lookup table. Instead, it employs a **Control Flow Graph (CFG) Flattening** technique using a massive binary decision tree (nested `if-else` blocks) to route execution based on the opcode `d`.

**Pattern:**
```lua
local d = e[Q] -- Load Opcode
if d < 55 then
    if d < 25 then
        -- Handle opcodes 0-24
    else
        -- Handle opcodes 25-54
    end
else
    -- Handle opcodes 55+
end
```
This structure makes static analysis difficult as there is no single "switch" statement to map; the logic is spread across hundreds of nested branches.

## Opcode Logic Classification

Based on pattern matching within the dispatch loop, we can classify several opcode behaviors:

1.  **Arithmetic & Logic:**
    *   **Addition:** `Z[u[Q]] = Z[Y[Q]] + Z[L[Q]]` (Opcode ~0x47)
    *   **Subtraction:** `Z[u[Q]] = Z[Y[Q]] - Z[L[Q]]` (Opcode ~0x49)
    *   **Multiplication:** `Z[Y[Q]] = Z[L[Q]] * Z[u[Q]]`
    *   **Modulo:** `Z[u[Q]] = Z[Y[Q]] % C[Q]`
    *   **Power:** `Z[u[Q]] = R[Q] ^ Z[L[Q]]`

2.  **Control Flow:**
    *   **Unconditional Jump:** `Q = u[Q]` (Sets the instruction pointer directly).
    *   **Conditional Jump:** `if not(Condition) then Q = u[Q] end`.
    *   **Return:** `return ...` (Exits the VM loop).

3.  **Memory & Data Access:**
    *   **Move:** `Z[Y[Q]] = Z[L[Q]]`
    *   **Load Constant:** `Z[Y[Q]] = H[Q]`
    *   **Table Access:** `Z[Y[Q]] = Z[L[Q]][Z[u[Q]]]`

4.  **Function Calls:**
    *   **Call:** Uses `i[...](...)` to bridge between the VM environment and the underlying Lua environment.
    *   **Varargs:** `Z[Y[Q]] = { ... }`.

## Notable Obfuscation Techniques

1.  **Mixed Radix Literals:** The code frequently switches between Hexadecimal (`0X...`) and Binary (`0B...`) notation, often using underscores (`0B10__1001__1`) to break regex searching and human readability.
2.  **Control Flow Flattening (CFF):**
    *   **VM Dispatch:** The opcode tree described above.
    *   **State Machines:** Functions like `Uk` use a `while true do if z > ...` loop driven by a state variable `z`. This hides the linear progression of initialization logic.
3.  **Structure of Arrays (SoA):** Splitting instructions into separate arrays (`e`, `u`, `Y`, `L`) prevents standard bytecode decompilers from recognizing the instruction format.
4.  **Bitwise Emulation:** Heavy use of `bit32` (or polyfills) to manage instruction decoding and logical operations, complicating the control flow analysis.
5.  **Variable Renaming:** All local variables are renamed to meaningless short identifiers (`O`, `X`, `z`, `I`) or garbage strings, and they are reused aggressively (Variable Recycling).
6.  **String Encryption:** Strings are likely stored in a packed binary format and decrypted at runtime via the loader `Ly`.
7.  **Dead Code / Junk Code:** The CFF loops likely contain unreachable branches or redundant calculations to confuse decompilers.

## High-Level Functionality Estimate
The script acts as a **secure loader and execution environment**.
1.  **Initialization (`ty`):** Sets up the environment and decrypts the payload.
2.  **Deserialization (`Ly`):** parses the encrypted bytecode string into the SoA format (`e`, `u`, `Y`, `L`).
3.  **Execution (`Ck`):** The VM loop interprets the custom opcodes, effectively running the original Lua script in a protected sandbox.
4.  **Purpose:** To protect the intellectual property of the underlying script (likely a game script, whitelist system, or proprietary logic) from theft or modification.

## Unclear / Ambiguous Sections
*   **Specific Opcode Mapping:** While the *classes* of opcodes are visible, the exact mapping of every ID (e.g., is Opcode 54 `ADD` or `SUB`?) is randomized and deeply nested. Recovering the exact instruction set requires dynamic analysis (tracing execution) or writing a parser for the decision tree.
*   **Payload Content:** The actual logic of the protected script is contained in the binary strings and cannot be determined statically without writing a decryptor/emulator for this specific Luraph version.
*   **`Uk` Function Role:** The function `Uk` implements a heavy CFF state machine. It is likely used for a specific high-security check (e.g., anti-tamper or environment verification) or the initial decryption phase, but its precise logic is opaque due to the flattening.

## Conclusion
The file is a robustly obfuscated Luraph v14 VM. It successfully hides the original source code by compiling it into a custom instruction set and embedding a complex interpreter to run it. Static analysis reveals the VM structure (Registers `Z`, SoA Instructions, Binary Tree Dispatch), but fully reversing the logic to source code would require building a dedicated de-obfuscator or dynamic tracer.
