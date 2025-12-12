#!/usr/bin/env lua5.1
-- Luraph v14 VM State Dumper
-- Hooks into the VM execution to extract bytecode and state

local dumper = {}
dumper.vm_state = {}
dumper.instructions = {}
dumper.constants = {}
dumper.upvalues = {}

-- Bytecode structure constants
dumper.LUA_VERSION = 0x51
dumper.LUAC_VERSION = 0x00
dumper.LUAC_FORMAT = 0
dumper.CHUNK_SIZE = 512

-- Lua 5.1 opcode definitions
dumper.opcodes = {
    MOVE = 0, LOADK = 1, LOADBOOL = 2, LOADNIL = 3, GETUPVAL = 4, GETGLOBAL = 5,
    GETTABLE = 6, SETGLOBAL = 7, SETTABLE = 8, NEWTABLE = 9, SELF = 10, ADD = 11,
    SUB = 12, MUL = 13, DIV = 14, MOD = 15, POW = 16, UNM = 17, NOT = 18, LEN = 19,
    CONCAT = 20, JMP = 21, EQ = 22, LT = 23, LE = 24, TEST = 25, TESTSET = 26,
    CALL = 27, TAILCALL = 28, RETURN = 29, FORLOOP = 30, FORPREP = 31, TFORLOOP = 32,
    SETLIST = 33, CLOSE = 34, CLOSURE = 35, VARARG = 36
}

function dumper.find_and_hook_vm()
    print("[*] Loading obfuscated script...")
    local script_path = arg[1] or "over.lua"
    
    local f = io.open(script_path, "rb")
    if not f then
        error("Cannot open " .. script_path)
    end
    local content = f:read("*a")
    f:close()
    
    print("[*] Script loaded: " .. #content .. " bytes")
    
    -- We'll need to modify the script to expose the VM state
    -- Create a wrapper that captures the VM's internal state
    
    local wrapper = [[
local original_script = function()
]] .. content .. [[
end

local hooked_return = original_script()

-- Capture the returned table
local vm_table = hooked_return

-- The VM table should contain the main execution functions
-- Try to access and dump the state
if vm_table and type(vm_table) == "table" then
    print("[+] Captured VM table with " .. countTable(vm_table) .. " keys")
    
    -- Look for instruction-related functions or data
    for k, v in pairs(vm_table) do
        if type(v) == "function" then
            print("[*] Found function: " .. tostring(k))
        elseif type(v) == "table" then
            print("[*] Found table: " .. tostring(k) .. " with " .. countTable(v) .. " elements")
        end
    end
end

function countTable(t)
    local count = 0
    for _ in pairs(t) do count = count + 1 end
    return count
end
]]
    
    return content, wrapper
end

function dumper.trace_vm_execution()
    print("\n=== VM Execution Tracer ===\n")
    
    -- Load the script and attempt to trace execution
    local content, wrapper = dumper.find_and_hook_vm()
    
    -- Create a modified environment with hooks
    local hooks = {
        instruction_count = 0,
        max_instructions = 10000,
        instructions = {},
    }
    
    -- We could use debug.sethook to trace the execution
    -- But that's complex with the obfuscated code
    
    -- Instead, analyze the structure statically
    return dumper.static_analysis(content)
end

function dumper.static_analysis(content)
    print("[*] Performing static analysis on obfuscated script...")
    
    -- Key patterns to look for in Luraph v14
    local patterns = {
        -- The main VM function (Ck) - handles instruction execution
        main_loop = "local d = %(e%[Q%]%)",
        -- Opcode dispatch
        dispatch = "if not%(d < ",
        -- Constants table
        constants = "H%[Q%]",
        -- Registers
        registers = "Z%[",
        -- Program counter
        pc = "Q %+= 1",
    }
    
    local findings = {}
    
    for name, pattern in pairs(patterns) do
        local count = select(2, content:gsub(pattern, ""))
        findings[name] = count
        print("[*] Pattern '" .. name .. "': found " .. count .. " times")
    end
    
    -- Try to identify function boundaries
    print("\n[*] Analyzing function structure...")
    local func_defs = {}
    local func_count = 0
    
    for name in content:gmatch("([A-Za-z_][A-Za-z0-9_]*)=function") do
        func_count = func_count + 1
        if not func_defs[name] then
            func_defs[name] = 0
        end
        func_defs[name] = func_defs[name] + 1
    end
    
    print("[*] Found " .. func_count .. " unique function assignments")
    
    -- Key functions we're looking for:
    local key_functions = {"Uk", "Ly", "Ck", "ty", "Jk"}
    for _, fname in ipairs(key_functions) do
        if content:find(fname .. "=function") then
            print("[+] Found key function: " .. fname)
        end
    end
    
    return findings
end

function dumper.reconstruct_bytecode()
    print("\n=== Bytecode Reconstruction ===\n")
    
    -- In a full implementation, we would:
    -- 1. Hook the Ly (loader) function to get instruction arrays
    -- 2. Extract constants, upvalues, prototypes
    -- 3. Reconstruct Lua 5.1 bytecode format
    -- 4. Write it to a .luac file
    
    print("[*] To fully deobfuscate, we would need to:")
    print("[1] Hook the instruction array loader (Ly function)")
    print("[2] Capture the bytecode during VM initialization")
    print("[3] Map SoA format to standard Lua bytecode")
    print("[4] Reconstruct function prototypes")
    
    print("\n[!] Note: Full deobfuscation requires dynamic execution hooking")
    print("[!] This would need to be done inside the Lua interpreter")
    
    return true
end

-- Main
if arg[0] and arg[0]:match("vm_dumper%.lua$") then
    dumper.trace_vm_execution()
    dumper.reconstruct_bytecode()
end

return dumper
