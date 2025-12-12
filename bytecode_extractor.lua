#!/usr/bin/env lua5.1
-- Luraph v14 Bytecode Extractor
-- Hooks into the VM to extract instruction streams and constants

local extractor = {}
extractor.vm_state = {}
extractor.captured_data = {}

-- Lua 5.1 bytecode header
function extractor.create_bytecode_header()
    local header = string.char(
        0x1B,  -- ESC
        0x4C,  -- 'L'
        0x75,  -- 'u'
        0x61   -- 'a'
    )
    header = header .. string.char(0x51)  -- Version 5.1
    header = header .. string.char(0x00)  -- Official version
    header = header .. string.char(0x01)  -- File format (1 = little-endian)
    header = header .. string.char(0x04)  -- sizeof(int)
    header = header .. string.char(0x08)  -- sizeof(size_t)
    header = header .. string.char(0x04)  -- sizeof(Instruction)
    header = header .. string.char(0x08)  -- sizeof(lua_Number)
    header = header .. string.char(0x00)  -- Lua number type (0 = double)
    return header
end

function extractor.int_to_bytes(n, size)
    local bytes = ""
    for i = 1, size do
        bytes = bytes .. string.char(bit32.band(bit32.rshift(n, 8 * (i - 1)), 0xFF))
    end
    return bytes
end

function extractor.size_t_to_bytes(n)
    return extractor.int_to_bytes(n, 8)
end

function extractor.write_string(s)
    -- Lua 5.1 bytecode string format: size_t length + data
    if not s then
        return extractor.size_t_to_bytes(0xFFFFFFFF)
    end
    local len = #s
    if len == 0 then
        return extractor.size_t_to_bytes(0xFFFFFFFF)
    end
    return extractor.size_t_to_bytes(len + 1) .. s .. string.char(0)
end

function extractor.hook_and_execute()
    print("[*] Loading obfuscated script...")
    
    -- Create a wrapper that captures the VM state
    local script_content = io.open("over.lua"):read("*a")
    
    -- Create a custom environment to intercept VM operations
    local env = {
        -- Standard library functions
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
    
    -- Intercept debug info if possible
    if debug then
        env.debug = debug
    end
    
    print("[*] Executing script in custom environment...")
    
    -- Set the environment and execute
    local func = loadstring(script_content)
    if func then
        setfenv(func, env)
        
        -- Try to capture the return value
        local success, result = pcall(func)
        
        if success then
            print("[+] Script executed successfully")
            
            if type(result) == "table" then
                print("[+] Captured table with " .. extractor.count_keys(result) .. " keys")
                
                -- Try to find the main execution function
                if result.Ck then
                    print("[+] Found Ck (main loop) function")
                end
                
                if result.Ly then
                    print("[+] Found Ly (loader) function")
                end
                
                -- Try to inspect the table structure
                for k, v in pairs(result) do
                    local vtype = type(v)
                    if vtype == "function" then
                        print("[*] " .. k .. " = function")
                    elseif vtype == "table" then
                        print("[*] " .. k .. " = table (" .. extractor.count_keys(v) .. " keys)")
                    else
                        print("[*] " .. k .. " = " .. vtype)
                    end
                end
            end
        else
            print("[-] Error executing script: " .. tostring(result))
        end
    else
        print("[-] Failed to load script")
    end
end

function extractor.count_keys(t)
    local count = 0
    for _ in pairs(t) do count = count + 1 end
    return count
end

function extractor.decompile_instructions(opcodes_array, args_a, args_b, args_c, constants)
    -- Convert instruction array format to a readable format
    
    print("\n=== Instruction Disassembly ===\n")
    
    if not opcodes_array or #opcodes_array == 0 then
        print("[-] No instructions found")
        return
    end
    
    local instruction_count = #opcodes_array
    print("[*] Total instructions: " .. instruction_count)
    
    -- The Luraph v14 VM maps opcodes to specific behaviors
    -- Standard Lua 5.1 has 36 opcodes (0-35)
    
    local opcode_names = {
        [0] = "MOVE",
        [1] = "LOADK",
        [2] = "LOADBOOL",
        [3] = "LOADNIL",
        [4] = "GETUPVAL",
        [5] = "GETGLOBAL",
        [6] = "GETTABLE",
        [7] = "SETGLOBAL",
        [8] = "SETTABLE",
        [9] = "NEWTABLE",
        [10] = "SELF",
        [11] = "ADD",
        [12] = "SUB",
        [13] = "MUL",
        [14] = "DIV",
        [15] = "MOD",
        [16] = "POW",
        [17] = "UNM",
        [18] = "NOT",
        [19] = "LEN",
        [20] = "CONCAT",
        [21] = "JMP",
        [22] = "EQ",
        [23] = "LT",
        [24] = "LE",
        [25] = "TEST",
        [26] = "TESTSET",
        [27] = "CALL",
        [28] = "TAILCALL",
        [29] = "RETURN",
        [30] = "FORLOOP",
        [31] = "FORPREP",
        [32] = "TFORLOOP",
        [33] = "SETLIST",
        [34] = "CLOSE",
        [35] = "CLOSURE",
        [36] = "VARARG",
    }
    
    -- Display first 20 instructions
    local display_count = math.min(20, instruction_count)
    for i = 1, display_count do
        local opcode = opcodes_array[i]
        local a = args_a and args_a[i] or 0
        local b = args_b and args_b[i] or 0
        local c = args_c and args_c[i] or 0
        
        local opname = opcode_names[opcode] or string.format("OP_%d", opcode)
        
        print(string.format("[%3d] %s\t\tA=%d\tB=%d\tC=%d", i-1, opname, a, b, c))
    end
    
    if instruction_count > 20 then
        print(string.format("[...] %d more instructions", instruction_count - 20))
    end
end

function extractor.run()
    print("\n" .. string.rep("=", 70))
    print("LURAPH V14 BYTECODE EXTRACTOR")
    print(string.rep("=", 70) .. "\n")
    
    print("[*] This tool attempts to extract bytecode from obfuscated Luraph scripts")
    print("[*] Note: Full extraction requires dynamic hooking into the VM\n")
    
    -- Try to hook and execute
    extractor.hook_and_execute()
    
    print("\n[*] Extraction complete")
    print("[!] For full bytecode extraction, use dynamic debugging")
    print("[!] Or modify the script to expose internal arrays\n")
end

-- Main execution
if arg[0] and arg[0]:match("bytecode_extractor%.lua$") then
    extractor.run()
end

return extractor
