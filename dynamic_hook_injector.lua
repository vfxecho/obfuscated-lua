#!/usr/bin/env lua5.1
-- Dynamic VM Hook Injector
-- Injects hooks into the running VM to capture internal state

local hook_injector = {
    state_capture = {},
    instruction_log = {},
    constants_captured = {},
    hooked = false,
}

function hook_injector.inject_hooks()
    print("[*] Initializing dynamic hook injection...")
    
    -- Global state for capturing
    local captured_state = {
        instruction_count = 0,
        total_executed = 0,
        instruction_history = {},
        function_calls = {},
    }
    
    -- Create a wrapper around loadstring to capture compilations
    local orig_loadstring = loadstring
    function _G.loadstring(str, name)
        if str and #str > 100 then
            print("[+] Captured loadstring call: " .. (name or "anonymous") .. " (" .. #str .. " bytes)")
            table.insert(captured_state.instruction_history, {
                type = "loadstring",
                size = #str,
                name = name,
            })
        end
        return orig_loadstring(str, name)
    end
    
    -- Hook into setfenv to detect environment changes
    local orig_setfenv = setfenv
    function _G.setfenv(func, env)
        if type(func) == "function" then
            local info = debug.getinfo(func)
            print("[+] setfenv called on function at: " .. (info.source or "unknown"))
            table.insert(captured_state.function_calls, {
                type = "setfenv",
                source = info.source,
                line = info.linedefined,
            })
        end
        return orig_setfenv(func, env)
    end
    
    -- Hook into getfenv
    local orig_getfenv = getfenv
    function _G.getfenv(func)
        local result = orig_getfenv(func)
        if type(func) == "function" then
            local info = debug.getinfo(func)
            print("[+] getfenv called on function at: " .. (info.source or "unknown"))
        end
        return result
    end
    
    return captured_state
end

function hook_injector.create_execution_wrapper()
    -- Wrapper script that executes the target and captures state
    local wrapper = [[
local hook_injector_state = {}

-- Load and execute the actual script
local script_content = ]] .. string.format("%q", io.open("over.lua"):read("*a")) .. [[

-- Parse the script looking for VM initialization
local function_defs = {}
for fname in script_content:gmatch("([A-Za-z_][A-Za-z0-9_]*)=function") do
    if not function_defs[fname] then
        function_defs[fname] = 0
    end
    function_defs[fname] = function_defs[fname] + 1
end

print("[+] Found function definitions:")
for fname, count in pairs(function_defs) do
    print("    " .. fname .. ": " .. count)
end

-- Load the script function
local script_func = loadstring(script_content)
if not script_func then
    error("Failed to load script")
end

-- Set up debug hooks before execution
if debug then
    local call_stack = {}
    local depth = 0
    
    local function debug_hook(event)
        if event == "call" then
            depth = depth + 1
            local info = debug.getinfo(2)
            call_stack[depth] = {
                name = info.name or "anonymous",
                source = info.source,
                line = info.currentline,
                depth = depth,
            }
            
            -- Look for key VM functions
            if info.name == "Ck" or info.name == "ty" or info.name == "Ly" then
                print("[+] Entering key VM function: " .. info.name .. " at depth " .. depth)
            end
        elseif event == "return" then
            depth = depth - 1
        end
    end
    
    -- Install the hook
    debug.sethook(debug_hook, "c")
end

-- Execute the script
print("[*] Executing obfuscated script...")
local success, result = pcall(script_func)

-- Remove hook
if debug then
    debug.sethook()
end

if success then
    print("[+] Script executed successfully")
    
    -- Inspect result
    if type(result) == "table" then
        local keys = {}
        for k in pairs(result) do
            table.insert(keys, k)
        end
        table.sort(keys)
        
        print("[+] Result table has " .. #keys .. " keys:")
        for i, k in ipairs(keys) do
            if i <= 20 then
                local v = result[k]
                print("    " .. k .. ": " .. type(v))
            end
        end
        
        if #keys > 20 then
            print("    ... and " .. (#keys - 20) .. " more")
        end
    else
        print("[!] Result type: " .. type(result))
    end
else
    print("[-] Execution failed: " .. tostring(result))
end

hook_injector_state.success = success
hook_injector_state.result = result
return hook_injector_state
]]
    
    return wrapper
end

function hook_injector.execute_with_hooks()
    print("\n[*] Creating wrapped execution environment...")
    
    -- Create wrapper
    local wrapper = hook_injector.create_execution_wrapper()
    
    -- Save wrapper to temp file
    local temp_file = "temp_wrapper.lua"
    local f = io.open(temp_file, "w")
    f:write(wrapper)
    f:close()
    
    print("[+] Wrapper created: " .. temp_file)
    print("[*] Executing with hooks...")
    
    -- Execute wrapper
    local func = loadstring(wrapper)
    if not func then
        print("[-] Failed to load wrapper")
        return nil
    end
    
    -- Execute
    local success, result = pcall(func)
    
    if success then
        print("[+] Wrapped execution completed")
        return result
    else
        print("[-] Wrapped execution failed: " .. tostring(result))
        return nil
    end
end

function hook_injector.analyze_captured_state(state)
    if not state then
        print("[-] No state to analyze")
        return
    end
    
    print("\n=== Captured State Analysis ===\n")
    
    -- This would analyze the captured state and extract:
    -- - Instruction arrays
    -- - Constants
    -- - Function prototypes
    -- - Call patterns
    
    print("[*] Analysis would extract:")
    print("    - Instruction arrays (e, u, Y, L, H)")
    print("    - Function prototypes")
    print("    - Upvalue information")
    print("    - Constant pool")
    print("    - Call stack information")
end

function hook_injector.run()
    print("\n" .. string.rep("=", 70))
    print("DYNAMIC VM HOOK INJECTOR")
    print(string.rep("=", 70) .. "\n")
    
    -- Inject hooks
    local captured = hook_injector.inject_hooks()
    
    -- Execute with hooks
    local state = hook_injector.execute_with_hooks()
    
    -- Analyze
    hook_injector.analyze_captured_state(state)
    
    print("\n[!] Hook injection complete")
    print("[!] For production use:")
    print("    1. Use this with a modified Lua interpreter")
    print("    2. Add breakpoints at specific addresses")
    print("    3. Dump memory when VM is in key functions")
    print("    4. Parse instruction arrays from memory")
end

if arg[0] and arg[0]:match("dynamic_hook_injector%.lua$") then
    hook_injector.run()
end

return hook_injector
