#!/usr/bin/env python3
"""
Luraph v14 Deobfuscator
Extracts and reconstructs bytecode from Luraph v14-obfuscated Lua scripts
"""

import sys
import re
import struct
import base64
import binascii
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional

@dataclass
class LuaOpcode:
    """Represents a Lua 5.1 opcode"""
    id: int
    name: str
    args: Tuple[str, ...]

class LuraphDeobfuscator:
    """Main deobfuscator class"""
    
    # Lua 5.1 opcodes
    OPCODES = {
        0: ("MOVE", ("A", "B")),
        1: ("LOADK", ("A", "Bx")),
        2: ("LOADBOOL", ("A", "B", "C")),
        3: ("LOADNIL", ("A", "B")),
        4: ("GETUPVAL", ("A", "B")),
        5: ("GETGLOBAL", ("A", "Bx")),
        6: ("GETTABLE", ("A", "B", "C")),
        7: ("SETGLOBAL", ("A", "Bx")),
        8: ("SETTABLE", ("A", "B", "C")),
        9: ("NEWTABLE", ("A", "B", "C")),
        10: ("SELF", ("A", "B", "C")),
        11: ("ADD", ("A", "B", "C")),
        12: ("SUB", ("A", "B", "C")),
        13: ("MUL", ("A", "B", "C")),
        14: ("DIV", ("A", "B", "C")),
        15: ("MOD", ("A", "B", "C")),
        16: ("POW", ("A", "B", "C")),
        17: ("UNM", ("A", "B")),
        18: ("NOT", ("A", "B")),
        19: ("LEN", ("A", "B")),
        20: ("CONCAT", ("A", "B", "C")),
        21: ("JMP", ("sBx",)),
        22: ("EQ", ("A", "B", "C")),
        23: ("LT", ("A", "B", "C")),
        24: ("LE", ("A", "B", "C")),
        25: ("TEST", ("A", "C")),
        26: ("TESTSET", ("A", "B", "C")),
        27: ("CALL", ("A", "B", "C")),
        28: ("TAILCALL", ("A", "B", "C")),
        29: ("RETURN", ("A", "B")),
        30: ("FORLOOP", ("A", "sBx")),
        31: ("FORPREP", ("A", "sBx")),
        32: ("TFORLOOP", ("A", "C")),
        33: ("SETLIST", ("A", "B", "C")),
        34: ("CLOSE", ("A",)),
        35: ("CLOSURE", ("A", "Bx")),
        36: ("VARARG", ("A", "B")),
    }
    
    def __init__(self, script_path: str):
        """Initialize the deobfuscator"""
        self.script_path = Path(script_path)
        self.content = None
        self.functions = {}
        self.constants = []
        self.instructions = []
        
    def load_script(self) -> str:
        """Load the obfuscated script"""
        if not self.script_path.exists():
            raise FileNotFoundError(f"Script not found: {self.script_path}")
        
        with open(self.script_path, 'r', encoding='utf-8', errors='ignore') as f:
            self.content = f.read()
        
        print(f"[*] Loaded script: {len(self.content)} bytes")
        return self.content
    
    def analyze_structure(self) -> Dict:
        """Analyze the structure of the obfuscated script"""
        if not self.content:
            self.load_script()
        
        analysis = {
            'total_size': len(self.content),
            'line_count': len(self.content.split('\n')),
            'function_count': len(re.findall(r'function\s*\(', self.content)),
            'function_defs': len(re.findall(r'([A-Za-z_]\w*)=function', self.content)),
            'has_ty_function': bool(re.search(r'ty\s*=\s*function|:ty\s*\(', self.content)),
        }
        
        print("\n=== Script Analysis ===\n")
        print(f"[*] Total size: {analysis['total_size']} bytes")
        print(f"[*] Line count: {analysis['line_count']}")
        print(f"[*] Inline functions: {analysis['function_count']}")
        print(f"[*] Named function assignments: {analysis['function_defs']}")
        print(f"[*] Has ty() function: {analysis['has_ty_function']}")
        
        return analysis
    
    def find_key_functions(self) -> Dict[str, Tuple[int, int]]:
        """Find locations of key functions in the script"""
        key_functions = ['Uk', 'Ly', 'Ck', 'ty', 'Jk', 'kk', 'qk', 'Qk']
        found = {}
        
        print("\n=== Key Functions ===\n")
        for func_name in key_functions:
            # Look for function definition
            pattern = rf'{func_name}\s*=\s*function'
            match = re.search(pattern, self.content)
            if match:
                start = match.start()
                found[func_name] = (start, start + 100)
                print(f"[+] Found {func_name} at offset {start}")
            else:
                print(f"[-] {func_name} not found")
        
        return found
    
    def extract_string_literals(self) -> List[str]:
        """Extract string literals from the script"""
        # Look for string patterns that might contain bytecode
        strings = re.findall(r'"([^"\\]|\\.)*"', self.content)
        strings += re.findall(r"'([^'\\]|\\.)*'", self.content)
        
        print(f"\n[*] Found {len(strings)} string literals")
        
        # Look for potentially encoded data
        potential_bytecode = [s for s in strings if len(s) > 100 or s.startswith('LPH')]
        print(f"[*] Found {len(potential_bytecode)} potential bytecode strings")
        
        return strings
    
    def identify_obfuscation_techniques(self) -> List[str]:
        """Identify obfuscation techniques used"""
        techniques = []
        
        # Check for mixed radix literals
        if re.search(r'0[Xx][0-9A-Fa-f]+|0[Bb][01_]+', self.content):
            techniques.append("Mixed radix literals (hex/binary)")
        
        # Check for control flow flattening
        if re.search(r'if\s+.*then.*else.*end\s+if', self.content):
            techniques.append("Control flow flattening")
        
        # Check for variable renaming (many single-letter variables)
        single_vars = len(re.findall(r'\b[a-z]\b(?!=|>|<|:)', self.content))
        if single_vars > 100:
            techniques.append(f"Variable renaming ({single_vars} single-letter vars)")
        
        # Check for structure of arrays
        if all(x in self.content for x in ['e[Q]', 'u[Q]', 'Y[Q]', 'L[Q]']):
            techniques.append("Structure of Arrays (SoA) instruction format")
        
        # Check for string concatenation/encryption
        if re.search(r'string\.char|string\.byte|bit32\.band|bit32\.bor', self.content):
            techniques.append("String manipulation/encryption")
        
        print("\n=== Obfuscation Techniques ===\n")
        for i, technique in enumerate(techniques, 1):
            print(f"[*] {i}. {technique}")
        
        return techniques
    
    def generate_report(self) -> str:
        """Generate a deobfuscation analysis report"""
        self.load_script()
        
        report = []
        report.append("=" * 70)
        report.append("LURAPH V14 DEOBFUSCATOR ANALYSIS REPORT")
        report.append("=" * 70)
        report.append("")
        
        # Basic analysis
        analysis = self.analyze_structure()
        
        # Find key functions
        functions = self.find_key_functions()
        
        # Extract strings
        strings = self.extract_string_literals()
        
        # Identify techniques
        techniques = self.identify_obfuscation_techniques()
        
        # VM Architecture
        report.append("\n=== VM ARCHITECTURE ===\n")
        
        if all(x in self.content for x in ['e[Q]', 'u[Q]', 'Y[Q]', 'L[Q]', 'H[Q]']):
            report.append("[+] Structure of Arrays (SoA) detected:")
            report.append("    - e[Q]: Opcode array")
            report.append("    - u[Q]: Operand A")
            report.append("    - Y[Q]: Operand B")
            report.append("    - L[Q]: Operand C")
            report.append("    - H[Q]: Constants table")
        
        # Check for main loop
        if 'repeat' in self.content and 'Q += 1' in self.content:
            report.append("[+] Main VM loop detected (repeat...until)")
        
        if 'if not(d <' in self.content:
            report.append("[+] Binary decision tree opcode dispatch detected")
        
        # Recommendations
        report.append("\n=== DEOBFUSCATION RECOMMENDATIONS ===\n")
        report.append("[1] Dynamic Execution Hooking:")
        report.append("    - Modify Lua interpreter to hook into VM functions")
        report.append("    - Capture instruction arrays (e, u, Y, L, H) during execution")
        report.append("    - Extract constants and function prototypes")
        report.append("")
        report.append("[2] Pattern-Based Opcode Mapping:")
        report.append("    - Analyze the binary decision tree to map opcodes")
        report.append("    - Cross-reference with Lua 5.1 standard opcodes")
        report.append("")
        report.append("[3] Bytecode Reconstruction:")
        report.append("    - Convert SoA format back to standard Lua format")
        report.append("    - Build proper function prototypes")
        report.append("    - Generate .luac file (Lua bytecode)")
        report.append("")
        report.append("[4] Decompilation:")
        report.append("    - Use Unluac or similar tool to decompile .luac")
        report.append("    - Reconstruct approximate source code")
        
        return "\n".join(report)
    
    def run(self):
        """Run the deobfuscator"""
        print("\n" + "=" * 70)
        print("LURAPH V14 DEOBFUSCATOR")
        print("=" * 70 + "\n")
        
        report = self.generate_report()
        print(report)
        
        # Write report to file
        report_path = self.script_path.parent / "ANALYSIS_REPORT.txt"
        with open(report_path, 'w') as f:
            f.write(report)
        
        print(f"\n[*] Report written to: {report_path}")

def main():
    """Main entry point"""
    script_path = Path(sys.argv[1] if len(sys.argv) > 1 else "over.lua")
    
    deobf = LuraphDeobfuscator(str(script_path))
    deobf.run()

if __name__ == '__main__':
    main()
