#!/usr/bin/env lua5.1
-- Advanced Luraph v14 VM State Extractor
-- Hooks into the VM to extract bytecode, constants, and function prototypes

local extractor = {
    vm_data = {},
    instructions = {},
    constants = {},
    functions = {},
}

-- Lua 5.1 constant types
local LUA_TNIL = 0
local LUA_TBOOLEAN = 1
local LUA_TNUMBER = 3
local LUA_TSTRING = 4
local LUA_TTABLE = 5
local LUA_TFUNCTION = 6

function extractor.setup_environment()
    print("[*] Setting up extraction environment...")
    
    -- Create a custom global environment
    local env = getfenv()
    
    -- Store original functions
    local orig_setmetatable = setmetatable
    local orig_getmetatable = getmetatable
    local orig_rawget = rawget
    local orig_rawset = rawset
    
    -- Create interception hooks
    local hooked_tables = {}
    
    function env.setmetatable(obj, mt)
        if type(obj) == "table" and mt and type(mt) == "table" then
            hooked_tables[obj] = mt
            print("[+] Hooked metatable for table")
        end
        return orig_setmetatable(obj, mt)
    end
    
    -- Wrap the script loading
    local original_loadstring = loadstring
    local captured_scripts = {}
    
    function env.loadstring(str, name)
        if str and #str > 1000 then
            print("[+] Captured large string load: " .. (#str) .. " bytes")
            table.insert(captured_scripts, {name = name, content = str})
        end
        return original_loadstring(str, name)
    end
    
    return env, captured_scripts, hooked_tables
end

function extractor.execute_with_hooks()
    print("\n=== Executing Script with Hooks ===\n")
    
    local env, captured_scripts, hooked_tables = extractor.setup_environment()
    
    -- Load the obfuscated script
    local script_file = io.open("over.lua", "rb")
    if not script_file then
        error("Cannot open over.lua")
    end
    local script_content = script_file:read("*a")
    script_file:close()
    
    print("[*] Loaded script: " .. #script_content .. " bytes")
    
    -- Compile the script
    local func, err = loadstring(script_content)
    if not func then
        print("[-] Failed to load: " .. tostring(err))
        return nil
    end
    
    -- Set custom environment
    setfenv(func, env)
    
    print("[*] Executing script...")
    
    -- Execute with error handling
    local success, result = pcall(func)
    
    if not success then
        print("[-] Execution error: " .. tostring(result))
        return nil
    end
    
    print("[+] Script executed successfully")
    
    if type(result) == "table" then
        print("[+] Got result table with " .. extractor.count_table(result) .. " keys")
        
        -- Inspect the returned table structure
        extractor.inspect_vm_table(result)
        
        return result, captured_scripts, hooked_tables
    end
    
    return nil, captured_scripts, hooked_tables
end

function extractor.count_table(t)
    local count = 0
    for _ in pairs(t) do
        count = count + 1
    end
    return count
end

function extractor.inspect_vm_table(vm_table)
    print("\n=== VM Table Structure ===\n")
    
    local function_count = 0
    local table_count = 0
    local other_count = 0
    
    for k, v in pairs(vm_table) do
        local vtype = type(v)
        if vtype == "function" then
            function_count = function_count + 1
            if function_count <= 5 then
                print("[+] Function: " .. tostring(k))
            end
        elseif vtype == "table" then
            table_count = table_count + 1
            local tsize = extractor.count_table(v)
            if table_count <= 5 then
                print("[+] Table: " .. tostring(k) .. " (" .. tsize .. " keys)")
            end
        else
            other_count = other_count + 1
        end
    end
    
    print("[*] Summary: " .. function_count .. " functions, " .. table_count .. " tables, " .. other_count .. " other")
end

function extractor.try_bytecode_recovery(vm_result)
    print("\n=== Attempting Bytecode Recovery ===\n")
    
    if not vm_result then
        print("[-] No VM result to recover from")
        return nil
    end
    
    -- The VM table should contain the main execution function (Ck)
    if vm_result.Ck and type(vm_result.Ck) == "function" then
        print("[+] Found Ck function (main execution loop)")
        
        -- Try to get function info
        local info = debug.getinfo(vm_result.Ck)
        if info then
            print("[*] Function source: " .. (info.source or "unknown"))
            print("[*] Function line range: " .. info.linedefined .. "-" .. info.lastlinedefined)
        end
    end
    
    -- Look for instruction-related data in the table
    local candidates = {}
    for k, v in pairs(vm_result) do
        if type(v) == "table" and #v > 10 then
            table.insert(candidates, {name = k, size = #v, type = type(v[1])})
        end
    end
    
    if #candidates > 0 then
        print("[+] Found " .. #candidates .. " large arrays that could contain instructions:")
        for i, cand in ipairs(candidates) do
            if i <= 10 then
                print("    " .. cand.name .. ": " .. cand.size .. " elements (type: " .. cand.type .. ")")
            end
        end
    end
    
    return candidates
end

function extractor.generate_lua_wrapper()
    -- Create a wrapper script that extracts the bytecode
    local wrapper = [[
local original = function()
]] .. io.open("over.lua"):read("*a") .. [[
end

-- Execute and capture
local success, vm_table = pcall(original)

if success and type(vm_table) == "table" then
    -- Try to access the internal state
    -- The main execution function should be Ck
    if vm_table.Ck then
        print("[+] VM successfully created")
        print("[+] Found Ck function")
        
        -- Try to call with dummy arguments to see what happens
        -- (This is dangerous and might fail)
        print("[!] Cannot directly inspect VM internals without execution context")
    end
else
    print("[-] Error creating VM: " .. tostring(vm_table))
end
]]
    
    return wrapper
end

function extractor.manual_disassembly()
    -- Parse the script to find SoA instruction arrays
    print("\n=== Manual Disassembly of SoA Arrays ===\n")
    
    local script = io.open("over.lua"):read("*a")
    
    -- Find references to e[Q], u[Q], Y[Q], L[Q]
    local patterns = {
        e_refs = #(script:match("[^e%[Q%]]*e%[Q%]") or "") > 0,
        u_refs = script:match("u%[Q%]") ~= nil,
        Y_refs = script:match("Y%[Q%]") ~= nil,
        L_refs = script:match("L%[Q%]") ~= nil,
        H_refs = script:match("H%[Q%]") ~= nil,
    }
    
    print("[+] Instruction array references found:")
    for name, found in pairs(patterns) do
        print("    " .. name .. ": " .. (found and "YES" or "NO"))
    end
    
    -- Find the opcode dispatch tree
    local dispatch_refs = 0
    for _ in script:gmatch("if not%(d < ") do
        dispatch_refs = dispatch_refs + 1
    end
    
    print("[+] Opcode dispatch branches: " .. dispatch_refs)
    
    -- Try to extract constant strings
    local strings = {}
    for str in script:gmatch('"([^"\\]|\\\\.)*"') do
        if #str > 20 then
            table.insert(strings, str)
        end
    end
    
    print("[+] Found " .. #strings .. " large string literals (potential encoded bytecode)")
    
    return patterns, dispatch_refs, strings
end

function extractor.create_extraction_script()
    -- This script will be executed inside a Lua environment to extract the bytecode
    local extraction_script = [[
-- Luraph v14 Bytecode Extraction Script
-- This runs inside the obfuscated VM environment

local debug_hook_enabled = false
local instruction_log = {}
local state_snapshots = {}

-- Try to enable debugging
if debug then
    local function hook_function(event, line)
        if event == "call" then
            local info = debug.getinfo(2, "nS")
            if info and info.what == "Lua" then
                if not state_snapshots[info.name] then
                    state_snapshots[info.name] = {
                        calls = 0,
                        source = info.source,
                        linedefined = info.linedefined,
                    }
                end
                state_snapshots[info.name].calls = state_snapshots[info.name].calls + 1
            end
        end
    end
    
    -- Enable the hook
    debug.sethook(hook_function, "c")
    debug_hook_enabled = true
end

-- Load and execute the main script
local result = (function()
]] .. io.open("over.lua"):read("*a") .. [[
end)()

-- Disable hook
if debug and debug_hook_enabled then
    debug.sethook()
end

-- Output what we captured
print("[*] Execution complete")
print("[*] State snapshots: " .. extractor.count_table(state_snapshots))

return result, state_snapshots
]]
    
    return extraction_script
end

function extractor.run()
    print("\n" .. string.rep("=", 70))
    print("ADVANCED LURAPH V14 BYTECODE EXTRACTOR")
    print(string.rep("=", 70) .. "\n")
    
    -- Stage 1: Manual disassembly
    extractor.manual_disassembly()
    
    print("\n" .. string.rep("-", 70) .. "\n")
    
    -- Stage 2: Execute with hooks
    local vm_result, captured_scripts, hooked_tables = extractor.execute_with_hooks()
    
    if vm_result then
        print("\n" .. string.rep("-", 70) .. "\n")
        
        -- Stage 3: Bytecode recovery attempt
        extractor.try_bytecode_recovery(vm_result)
    end
    
    print("\n[!] Full bytecode extraction requires:")
    print("    1. Modified Lua interpreter with extended debugging")
    print("    2. Breakpoints in the VM initialization (ty) function")
    print("    3. Capture of instruction arrays (e, u, Y, L, H)")
    print("    4. Reconstruction to standard Lua bytecode format")
end

if arg[0] and arg[0]:match("advanced_extractor%.lua$") then
    extractor.run()
end

return extractor
