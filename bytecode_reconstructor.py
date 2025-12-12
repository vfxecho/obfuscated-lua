#!/usr/bin/env python3
"""
Luraph v14 Bytecode Reconstructor
Reconstructs standard Lua 5.1 bytecode from extracted instruction data
"""

import struct
import sys
from typing import List, Tuple, Optional
from pathlib import Path

class LuaBytecodeReconstructor:
    """Reconstructs Lua 5.1 bytecode from Luraph v14 VM state"""
    
    # Lua 5.1 header values
    LUA_SIGNATURE = b'\x1bLua'
    LUAC_VERSION = 0x51  # Lua 5.1
    LUAC_FORMAT = 0
    LUAC_DATA = b'\x19\x93\r\n\x1a\n'  # Test number: 1.0
    
    # Lua 5.1 opcodes
    OPCODES = {
        'MOVE': 0, 'LOADK': 1, 'LOADBOOL': 2, 'LOADNIL': 3,
        'GETUPVAL': 4, 'GETGLOBAL': 5, 'GETTABLE': 6, 'SETGLOBAL': 7,
        'SETTABLE': 8, 'NEWTABLE': 9, 'SELF': 10, 'ADD': 11,
        'SUB': 12, 'MUL': 13, 'DIV': 14, 'MOD': 15,
        'POW': 16, 'UNM': 17, 'NOT': 18, 'LEN': 19,
        'CONCAT': 20, 'JMP': 21, 'EQ': 22, 'LT': 23,
        'LE': 24, 'TEST': 25, 'TESTSET': 26, 'CALL': 27,
        'TAILCALL': 28, 'RETURN': 29, 'FORLOOP': 30, 'FORPREP': 31,
        'TFORLOOP': 32, 'SETLIST': 33, 'CLOSE': 34, 'CLOSURE': 35,
        'VARARG': 36
    }
    
    def __init__(self):
        self.instructions = []
        self.constants = []
        self.upvalues = []
        self.prototypes = []
        self.source = "obfuscated.lua"
        
    def create_header(self) -> bytes:
        """Create Lua 5.1 bytecode header"""
        header = self.LUA_SIGNATURE
        header += struct.pack('B', self.LUAC_VERSION)
        header += struct.pack('B', self.LUAC_FORMAT)
        header += self.LUAC_DATA
        header += struct.pack('B', 4)  # sizeof(int)
        header += struct.pack('B', 8)  # sizeof(size_t)
        header += struct.pack('B', 4)  # sizeof(Instruction)
        header += struct.pack('B', 8)  # sizeof(lua_Number)
        header += struct.pack('B', 0)  # lua number type (double)
        return header
    
    def write_string(self, s: Optional[str]) -> bytes:
        """Write a string in Lua bytecode format"""
        if s is None:
            return struct.pack('<I', 0xFFFFFFFF)
        
        encoded = s.encode('utf-8') if isinstance(s, str) else s
        size = len(encoded)
        
        if size > 0xFFFFFFFE:
            # String too large
            return struct.pack('<I', 0xFFFFFFFF)
        
        # Format: size_t (4 bytes) + data
        return struct.pack('<I', size + 1) + encoded + b'\x00'
    
    def write_number(self, n: float) -> bytes:
        """Write a number in Lua bytecode format"""
        return struct.pack('<d', n)  # Double precision
    
    def write_int(self, i: int) -> bytes:
        """Write an integer in Lua bytecode format"""
        return struct.pack('<i', i)
    
    def encode_instruction(self, opcode: int, a: int, b: int, c: int) -> int:
        """Encode an instruction word (Lua 5.1 format)
        
        Format:
        - opcode: 6 bits (0-5)
        - A: 8 bits (6-13)
        - B: 9 bits (14-22)
        - C: 9 bits (23-31)
        """
        instruction = opcode & 0x3F
        instruction |= (a & 0xFF) << 6
        instruction |= (b & 0x1FF) << 14
        instruction |= (c & 0x1FF) << 23
        return instruction
    
    def create_simple_function(self, instructions_data: List[Tuple[int, int, int, int]],
                              constants_data: List[object] = None) -> bytes:
        """Create a simple function prototype in Lua bytecode format"""
        
        bytecode = b''
        
        # Write source
        bytecode += self.write_string(self.source)
        
        # Line defined (start)
        bytecode += self.write_int(1)
        
        # Last line defined (end)
        bytecode += self.write_int(len(instructions_data) if instructions_data else 1)
        
        # Upvalues count
        bytecode += struct.pack('B', len(self.upvalues))
        
        # Parameters count
        bytecode += struct.pack('B', 0)
        
        # Vararg flag
        bytecode += struct.pack('B', 2)  # VAR_VARARG
        
        # Stack size (estimate)
        bytecode += struct.pack('B', 2)
        
        # Write instructions
        instructions = instructions_data or []
        bytecode += self.write_int(len(instructions))
        
        for opcode, a, b, c in instructions:
            instr = self.encode_instruction(opcode, a, b, c)
            bytecode += struct.pack('<I', instr)
        
        # Write constants
        constants = constants_data or []
        bytecode += self.write_int(len(constants))
        
        for const in constants:
            if const is None:
                bytecode += struct.pack('B', 0)  # NIL
            elif isinstance(const, bool):
                bytecode += struct.pack('B', 1)  # BOOLEAN
                bytecode += struct.pack('B', 1 if const else 0)
            elif isinstance(const, (int, float)):
                bytecode += struct.pack('B', 3)  # NUMBER
                bytecode += self.write_number(float(const))
            elif isinstance(const, str):
                bytecode += struct.pack('B', 4)  # STRING
                bytecode += self.write_string(const)
        
        # Write function prototypes (none for simple function)
        bytecode += self.write_int(0)
        
        # Write upvalue info (empty)
        bytecode += self.write_int(len(self.upvalues))
        for _ in range(len(self.upvalues)):
            bytecode += struct.pack('BB', 0, 0)
        
        return bytecode
    
    def reconstruct_from_soa(self, opcodes: List[int], args_a: List[int],
                             args_b: List[int], args_c: List[int],
                             constants: List[object] = None) -> bytes:
        """Reconstruct bytecode from Structure of Arrays format"""
        
        print("[*] Reconstructing from SoA format...")
        print(f"[*] Instructions: {len(opcodes)}")
        print(f"[*] Constants: {len(constants or [])}")
        
        # Create header
        bytecode = self.create_header()
        
        # Convert SoA to instruction list
        instructions = []
        for i in range(len(opcodes)):
            opcode = opcodes[i]
            a = args_a[i] if i < len(args_a) else 0
            b = args_b[i] if i < len(args_b) else 0
            c = args_c[i] if i < len(args_c) else 0
            instructions.append((opcode, a, b, c))
        
        # Create function prototype
        func_bytecode = self.create_simple_function(instructions, constants)
        bytecode += func_bytecode
        
        return bytecode
    
    def create_test_bytecode(self) -> bytes:
        """Create a test bytecode with a simple 'return 1' function"""
        
        print("[*] Creating test bytecode (return 1)...")
        
        bytecode = self.create_header()
        
        # Simple function: return 1
        # LOADK 0, 0    ; Load constant 0 into register 0
        # RETURN 0, 2   ; Return value in register 0
        
        instructions = [
            (self.OPCODES['LOADK'], 0, 0, 0),  # LOADK A=0, Bx=0
            (self.OPCODES['RETURN'], 0, 2, 0), # RETURN A=0, B=2
        ]
        
        constants = [1]  # Constant 0 = 1
        
        func_bytecode = self.create_simple_function(instructions, constants)
        bytecode += func_bytecode
        
        return bytecode
    
    def save_bytecode(self, bytecode: bytes, filename: str = "output.luac"):
        """Save bytecode to file"""
        path = Path(filename)
        with open(path, 'wb') as f:
            f.write(bytecode)
        print(f"[+] Bytecode saved to: {path}")
        print(f"[+] File size: {len(bytecode)} bytes")
        return path

class BytecodeAnalyzer:
    """Analyzes bytecode to extract opcodes"""
    
    def __init__(self, script_path: str = "over.lua"):
        self.script_path = script_path
        self.opcodes = []
        self.constants = []
        
    def analyze_dispatch_tree(self) -> dict:
        """Analyze the opcode dispatch tree to map opcodes"""
        
        print("[*] Analyzing opcode dispatch tree...")
        
        with open(self.script_path, 'r') as f:
            content = f.read()
        
        # Find all "if not(d < X)" patterns
        import re
        patterns = re.findall(r'if not\(d < (\d+)\)', content)
        
        print(f"[+] Found {len(patterns)} dispatch points")
        
        # Build decision tree
        decision_tree = {}
        for pattern in patterns:
            threshold = int(pattern)
            if threshold not in decision_tree:
                decision_tree[threshold] = []
        
        return decision_tree
    
    def extract_strings(self) -> List[str]:
        """Extract large strings that might be encoded bytecode"""
        
        print("[*] Extracting string literals...")
        
        with open(self.script_path, 'r') as f:
            content = f.read()
        
        # Find long strings
        import re
        strings = re.findall(r'"([^"]{100,})"', content)
        
        print(f"[+] Found {len(strings)} large strings")
        
        return strings
    
    def save_analysis(self, filename: str = "opcode_analysis.txt"):
        """Save analysis results"""
        
        analysis = f"""Luraph v14 Opcode Analysis
{'='*50}

Dispatch Tree Points: {len(self.analyze_dispatch_tree())}
Large Strings Found: {len(self.extract_strings())}

Note: Full analysis requires dynamic execution hooking
"""
        
        with open(filename, 'w') as f:
            f.write(analysis)
        
        print(f"[+] Analysis saved to: {filename}")

def main():
    print("\n" + "="*70)
    print("LURAPH V14 BYTECODE RECONSTRUCTOR")
    print("="*70 + "\n")
    
    # Analyze the script
    analyzer = BytecodeAnalyzer("over.lua")
    dispatch_tree = analyzer.analyze_dispatch_tree()
    strings = analyzer.extract_strings()
    analyzer.save_analysis()
    
    print("\n" + "-"*70 + "\n")
    
    # Create reconstructor
    reconstructor = LuaBytecodeReconstructor()
    
    # Try to create test bytecode first
    print("\n[*] Creating test bytecode...")
    test_bytecode = reconstructor.create_test_bytecode()
    reconstructor.save_bytecode(test_bytecode, "test_simple.luac")
    
    print("\n[!] For full reconstruction, you need to:")
    print("    1. Hook into the VM execution")
    print("    2. Extract the instruction arrays (e, u, Y, L, H)")
    print("    3. Pass them to reconstruct_from_soa()")
    print("    4. Save the resulting bytecode")
    print("")
    print("    Example:")
    print("    reconstructor.reconstruct_from_soa(e, u, Y, L, H)")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
