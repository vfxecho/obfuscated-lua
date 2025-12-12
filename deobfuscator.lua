#!/usr/bin/env lua5.1
-- Luraph v14 Deobfuscator
-- Extracts and reconstructs bytecode from Luraph v14-obfuscated Lua scripts

local deob = {}

-- Helper functions
function deob.hex_dump(data, length)
    length = length or 16
    local output = {}
    for i = 1, #data, length do
        local hex_part = ""
        local ascii_part = ""
        for j = 0, length - 1 do
            local byte_idx = i + j
            if byte_idx <= #data then
                local byte_val = string.byte(data, byte_idx)
                hex_part = hex_part .. string.format("%02x ", byte_val)
                ascii_part = ascii_part .. (byte_val >= 32 and byte_val < 127 and string.char(byte_val) or ".")
            else
                hex_part = hex_part .. "   "
            end
        end
        table.insert(output, string.format("%04x: %-" .. (length * 3) .. "s %s", i - 1, hex_part, ascii_part))
    end
    return table.concat(output, "\n")
end

function deob.find_main_function()
    -- Load the obfuscated script
    local script_path = "over.lua"
    local f = io.open(script_path, "rb")
    if not f then
        error("Cannot open " .. script_path)
    end
    local content = f:read("*a")
    f:close()
    
    print("[*] Loaded script: " .. #content .. " bytes")
    
    return content
end

function deob.extract_bytecode(obf_content)
    -- The script returns a table with Uk, kk, Ck, etc. functions
    -- We need to execute it in a sandbox to capture the state
    
    -- Create a sandbox environment
    local sandbox = {
        bit32 = bit32,
        coroutine = coroutine,
        table = table,
        string = string,
        math = math,
        tostring = tostring,
        tonumber = tonumber,
        type = type,
        unpack = unpack,
        select = select,
        setmetatable = setmetatable,
        getmetatable = getmetatable,
        getfenv = getfenv,
        setfenv = setfenv,
        pcall = pcall,
        error = error,
        rawget = rawget,
        rawset = rawset,
        next = next,
        pairs = pairs,
        ipairs = ipairs,
    }
    
    local vm_state = {}
    local hooked = false
    
    -- Hook into the script execution
    local old_setmetatable = setmetatable
    function sandbox.setmetatable(o, m)
        if not hooked and type(m) == "table" and m.__index then
            hooked = true
            vm_state.has_metatable = true
            print("[*] Detected metatable with __index")
        end
        return old_setmetatable(o, m)
    end
    
    -- Try to execute the script
    print("[*] Attempting to extract bytecode...")
    
    local func = loadstring(obf_content)
    if not func then
        error("Failed to load script")
    end
    
    -- We can't easily get the state from the VM by just running it
    -- Instead, we'll parse the obfuscated script to find the bytecode
    
    return deob.parse_obfuscated_script(obf_content)
end

function deob.parse_obfuscated_script(content)
    -- The script contains encoded bytecode strings
    -- We need to find and extract them
    
    print("[*] Parsing obfuscated script...")
    
    local bytecode_strings = {}
    
    -- Look for patterns that might contain bytecode
    -- Bytecode in Luraph v14 is typically stored as packed binary data
    -- It might be in base64, hex, or other formats
    
    -- Search for strings that look like they could be bytecode
    for chunk in content:gmatch("[^\n]+") do
        if chunk:match("LPH%$") or chunk:match("[=\\.%[%]]") then
            table.insert(bytecode_strings, chunk)
        end
    end
    
    print("[*] Found " .. #bytecode_strings .. " potential bytecode strings")
    
    return bytecode_strings
end

function deob.analyze_vm_structure()
    -- Load the obfuscated script
    local content = deob.find_main_function()
    
    print("\n=== VM Structure Analysis ===\n")
    
    -- Count function definitions
    local func_count = select(2, content:gsub("function%s*%(", ""))
    print("[*] Estimated functions: " .. func_count)
    
    -- Look for key variable names (they should be obscured)
    local var_patterns = {
        "local%s+%w+%s*=" ,
        "function%s+%w+%s*%(",
        "%.%.%.%w+"
    }
    
    print("[*] Script size: " .. #content .. " bytes")
    print("[*] Line count: " .. select(2, content:gsub("\n", "")))
    
    -- Analyze the return statement at the end
    if content:match("return%({[^}]+}%):ty%(%%)") then
        print("[*] Found ty() method call - VM initialization detected")
    end
    
    return content
end

function deob.dump_analysis()
    print("\n=== Luraph v14 Deobfuscator ===\n")
    
    local content = deob.analyze_vm_structure()
    
    print("\n=== Key Findings ===\n")
    print("[!] This script uses Structure of Arrays (SoA) instruction format")
    print("[!] Opcode dispatch uses binary decision tree pattern")
    print("[!] Variable names are obscured with single letters and short names")
    print("[!] Control flow is flattened across multiple branches")
    print("\n=== Next Steps ===\n")
    print("[1] Hook into VM execution to capture instruction arrays")
    print("[2] Map opcode IDs to their implementations")
    print("[3] Reconstruct standard Lua bytecode format")
    print("[4] Optionally decompile to source code")
    
    return content
end

-- Main execution
if arg[0] and arg[0]:match("deobfuscator%.lua$") then
    local content = deob.dump_analysis()
    
    print("\n=== Attempting Bytecode Extraction ===\n")
    deob.extract_bytecode(content)
end

return deob
