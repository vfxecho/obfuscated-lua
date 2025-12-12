#!/usr/bin/env python3
"""
Luraph v14 Opcode Mapper
Analyzes the binary decision tree to map obfuscated opcodes to Lua 5.1 standard opcodes
"""

import re
from typing import Dict, List, Set, Tuple
from pathlib import Path
import ast

class OpcodeMapper:
    """Maps Luraph v14 opcodes to standard Lua 5.1 opcodes"""
    
    # Lua 5.1 standard opcodes
    STANDARD_OPCODES = {
        0: 'MOVE', 1: 'LOADK', 2: 'LOADBOOL', 3: 'LOADNIL',
        4: 'GETUPVAL', 5: 'GETGLOBAL', 6: 'GETTABLE', 7: 'SETGLOBAL',
        8: 'SETTABLE', 9: 'NEWTABLE', 10: 'SELF', 11: 'ADD',
        12: 'SUB', 13: 'MUL', 14: 'DIV', 15: 'MOD',
        16: 'POW', 17: 'UNM', 18: 'NOT', 19: 'LEN',
        20: 'CONCAT', 21: 'JMP', 22: 'EQ', 23: 'LT',
        24: 'LE', 25: 'TEST', 26: 'TESTSET', 27: 'CALL',
        28: 'TAILCALL', 29: 'RETURN', 30: 'FORLOOP', 31: 'FORPREP',
        32: 'TFORLOOP', 33: 'SETLIST', 34: 'CLOSE', 35: 'CLOSURE',
        36: 'VARARG'
    }
    
    # Operation patterns that identify opcode behavior
    OPERATION_PATTERNS = {
        'ADD': [r'Z\[u\[Q\]\]\s*=.*\+', r'\+.*Z\['],
        'SUB': [r'Z\[u\[Q\]\]\s*=.*\-', r'\-.*Z\['],
        'MUL': [r'Z\[.*\]\s*=.*\*', r'\*.*Z\['],
        'DIV': [r'Z\[.*\]\s*=/'],
        'MOD': [r'Z\[.*\]\s*=%'],
        'POW': [r'Z\[.*\]\s*=.*\^'],
        'MOVE': [r'Z\[u\[Q\]\]\s*=Z\['],
        'LOADK': [r'Z\[.*\]\s*=H\[Q\]'],
        'NEWTABLE': [r'Z\[.*\]\s*=\{\}'],
        'CALL': [r'Z\[.*\]\('],
        'RETURN': [r'return\s+(false|true)', r'Z\[.*\].*return'],
        'JMP': [r'Q\s*=\s*u\[Q\]', r'Q\s*=\s*L\[Q\]'],
        'GETTABLE': [r'Z\[.*\]\s*=Z\[.*\]\[Z\['],
        'SETTABLE': [r'Z\[.*\]\[Z\[.*\]\]\s*='],
    }
    
    def __init__(self, script_path: str = "over.lua"):
        self.script_path = Path(script_path)
        self.content = None
        self.opcode_map = {}
        self.load_script()
    
    def load_script(self):
        """Load the obfuscated script"""
        with open(self.script_path, 'r', errors='ignore') as f:
            self.content = f.read()
        print(f"[+] Loaded script: {len(self.content)} bytes")
    
    def extract_dispatch_tree(self) -> Dict:
        """Extract the binary decision tree structure"""
        print("\n[*] Extracting opcode dispatch tree...")
        
        tree = {}
        
        # Find all conditional branches
        # Pattern: if not(d < X) then ... else ... end
        pattern = r'if\s+not\(d\s*<\s*(\d+)\)\s*then\s*(.*?)\s*else\s*(.*?)(?=end|else|if)'
        
        for match in re.finditer(pattern, self.content, re.DOTALL):
            threshold = int(match.group(1))
            true_branch = match.group(2)
            false_branch = match.group(3)
            
            tree[threshold] = {
                'threshold': threshold,
                'true_branch': true_branch[:200],  # First 200 chars
                'false_branch': false_branch[:200],
            }
        
        print(f"[+] Found {len(tree)} branch points")
        return tree
    
    def analyze_opcode_behavior(self, opcode_id: int, code_block: str) -> List[str]:
        """Analyze code block to identify opcode behavior"""
        
        matches = []
        
        for op_name, patterns in self.OPERATION_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, code_block, re.IGNORECASE):
                    matches.append(op_name)
        
        return list(set(matches))  # Remove duplicates
    
    def build_opcode_mapping(self) -> Dict[int, Dict]:
        """Build the opcode mapping"""
        print("\n[*] Building opcode mapping...")
        
        tree = self.extract_dispatch_tree()
        
        opcode_info = {}
        
        # Try to map based on tree structure and behavior analysis
        threshold_list = sorted(tree.keys())
        
        for i, threshold in enumerate(threshold_list):
            branch = tree[threshold]
            
            # Analyze behavior
            behaviors = self.analyze_opcode_behavior(i, branch['true_branch'])
            
            opcode_info[i] = {
                'id': i,
                'threshold': threshold,
                'detected_behavior': behaviors,
                'confidence': len(behaviors) > 0,
            }
        
        return opcode_info
    
    def find_arithmetic_opcodes(self) -> Dict[str, int]:
        """Find arithmetic opcode patterns"""
        print("\n[*] Searching for arithmetic opcodes...")
        
        arithmetic = {}
        
        patterns = {
            'ADD': r'Z\[u\[Q\]\]\s*=\s*\(Z\[Y\[Q\]\]\s*\+Z\[L\[Q\]\]\)',
            'SUB': r'Z\[u\[Q\]\]\s*=\s*\(Z\[Y\[Q\]\]\s*\-Z\[L\[Q\]\]\)',
            'MUL': r'Z\[Y\[Q\]\]\s*=\s*\(Z\[L\[Q\]\]\s*\*Z\[u\[Q\]\]\)',
            'DIV': r'Z\[.*\]\s*=\s*\(Z\[.*\]/Z\[.*\]\)',
            'MOD': r'Z\[u\[Q\]\]\s*=\s*\(Z\[Y\[Q\]\]\s*%',
        }
        
        for op_name, pattern in patterns.items():
            if re.search(pattern, self.content):
                print(f"[+] Found {op_name} pattern")
                arithmetic[op_name] = len(re.findall(pattern, self.content))
        
        return arithmetic
    
    def find_jump_opcodes(self) -> Dict[str, List[str]]:
        """Find jump instruction patterns"""
        print("\n[*] Searching for jump/control flow opcodes...")
        
        jumps = {
            'JMP': [],
            'CJMP': [],
            'RETURN': [],
        }
        
        # Find unconditional jumps
        jmp_pattern = r'Q\s*=\s*(?:u\[Q\]|Y\[Q\]|L\[Q\])\s*;'
        for match in re.finditer(jmp_pattern, self.content):
            context = self.content[max(0, match.start()-50):match.start()+50]
            jumps['JMP'].append(context)
        
        if jumps['JMP']:
            print(f"[+] Found {len(jumps['JMP'])} unconditional jumps")
        
        # Find conditional jumps
        cjmp_pattern = r'if\s+(?:not\s*)?\(Z\[.*?\]\).*?then\s+Q\s*=.*?end'
        for match in re.finditer(cjmp_pattern, self.content):
            context = self.content[max(0, match.start()-50):match.start()+100]
            jumps['CJMP'].append(context)
        
        if jumps['CJMP']:
            print(f"[+] Found {len(jumps['CJMP'])} conditional jumps")
        
        # Find returns
        return_pattern = r'return\s+(?:false|true|.*?)'
        for match in re.finditer(return_pattern, self.content):
            context = self.content[max(0, match.start()-50):match.start()+50]
            jumps['RETURN'].append(context)
        
        return jumps
    
    def find_memory_opcodes(self) -> Dict[str, int]:
        """Find memory access opcodes"""
        print("\n[*] Searching for memory access opcodes...")
        
        memory = {}
        
        patterns = {
            'MOVE': r'Z\[u\[Q\]\]\s*=Z\[Y\[Q\]\]',
            'LOADK': r'Z\[Y\[Q\]\]\s*=H\[Q\]',
            'GETTABLE': r'Z\[Y\[Q\]\]\s*=Z\[L\[Q\]\]\[Z\[u\[Q\]\]\]',
            'SETTABLE': r'Z\[Y\[Q\]\]\[Z\[L\[Q\]\]\]\s*=H\[Q\]',
            'LOADNIL': r'for.*in.*Z\).*nil',
            'NEWTABLE': r'Z\[.*\]\s*=\{\}',
        }
        
        for op_name, pattern in patterns.items():
            count = len(re.findall(pattern, self.content))
            if count > 0:
                print(f"[+] Found {op_name}: {count} instances")
                memory[op_name] = count
        
        return memory
    
    def generate_mapping_report(self) -> str:
        """Generate a detailed mapping report"""
        print("\n[*] Generating mapping report...")
        
        report = "Luraph v14 Opcode Mapping Analysis\n"
        report += "=" * 60 + "\n\n"
        
        # Arithmetic opcodes
        arithmetic = self.find_arithmetic_opcodes()
        report += "ARITHMETIC OPCODES\n" + "-" * 60 + "\n"
        for op, count in arithmetic.items():
            report += f"  {op}: {count} instances\n"
        
        report += "\n"
        
        # Memory opcodes
        memory = self.find_memory_opcodes()
        report += "MEMORY OPCODES\n" + "-" * 60 + "\n"
        for op, count in memory.items():
            report += f"  {op}: {count} instances\n"
        
        report += "\n"
        
        # Jump opcodes
        jumps = self.find_jump_opcodes()
        report += "JUMP/CONTROL OPCODES\n" + "-" * 60 + "\n"
        for op, instances in jumps.items():
            report += f"  {op}: {len(instances)} instances\n"
        
        report += "\nMAPPING SUMMARY\n" + "-" * 60 + "\n"
        report += "Total Identified Opcodes: " + str(len(arithmetic) + len(memory) + sum(len(v) for v in jumps.values())) + "\n"
        report += "Standard Lua 5.1 Opcodes: 37\n"
        
        report += "\nNOTE: For complete opcode mapping, dynamic execution analysis is required.\n"
        report += "Static analysis can identify patterns, but exact opcode assignments\n"
        report += "require capturing the VM state during execution.\n"
        
        return report

def main():
    print("\n" + "="*70)
    print("LURAPH V14 OPCODE MAPPER")
    print("="*70 + "\n")
    
    mapper = OpcodeMapper("over.lua")
    
    # Perform analysis
    report = mapper.generate_mapping_report()
    
    print("\n" + report)
    
    # Save report
    with open("opcode_mapping_report.txt", "w") as f:
        f.write(report)
    
    print("[+] Report saved to: opcode_mapping_report.txt")
    
    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main())
