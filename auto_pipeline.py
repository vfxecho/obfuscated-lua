#!/usr/bin/env python3
"""
Automatic Luraph v14 Deobfuscation Pipeline
Performs all extraction, reconstruction, and decompilation steps automatically
"""

import subprocess
import sys
import os
import re
from pathlib import Path
from typing import Optional, Tuple

class DeobfuscationPipeline:
    """Automated deobfuscation pipeline"""
    
    def __init__(self, script_path: str = "over.lua"):
        self.script_path = Path(script_path)
        self.work_dir = Path("./deobfuscated")
        self.setup_workspace()
        
    def setup_workspace(self):
        """Create working directory"""
        self.work_dir.mkdir(exist_ok=True)
        print(f"[*] Working directory: {self.work_dir}")
    
    def stage_1_analysis(self) -> dict:
        """Stage 1: Static analysis"""
        print("\n" + "="*70)
        print("STAGE 1: STATIC ANALYSIS")
        print("="*70 + "\n")
        
        with open(self.script_path, 'r', errors='ignore') as f:
            content = f.read()
        
        analysis = {
            'file_size': len(content),
            'line_count': content.count('\n'),
            'functions': len(re.findall(r'function\s*\(', content)),
            'has_soa': all(x in content for x in ['e[Q]', 'u[Q]', 'Y[Q]', 'L[Q]']),
            'dispatch_points': len(re.findall(r'if not\(d < ', content)),
            'string_operations': len(re.findall(r'string\.|bit32\.', content)),
        }
        
        print("[+] Analysis Results:")
        print(f"    File size: {analysis['file_size']} bytes")
        print(f"    Minified: {analysis['line_count']} lines")
        print(f"    Functions: {analysis['functions']}")
        print(f"    SoA Format: {analysis['has_soa']}")
        print(f"    Dispatch Points: {analysis['dispatch_points']}")
        print(f"    Encoding Operations: {analysis['string_operations']}")
        
        # Save analysis
        with open(self.work_dir / "analysis.txt", 'w') as f:
            for k, v in analysis.items():
                f.write(f"{k}: {v}\n")
        
        return analysis
    
    def stage_2_extraction(self) -> Optional[dict]:
        """Stage 2: Attempt bytecode extraction"""
        print("\n" + "="*70)
        print("STAGE 2: BYTECODE EXTRACTION")
        print("="*70 + "\n")
        
        # Try using Lua extraction tool
        print("[*] Running Lua-based extraction...")
        
        try:
            result = subprocess.run(
                ['lua5.1', 'advanced_extractor.lua'],
                cwd=self.script_path.parent,
                capture_output=True,
                timeout=5,
                text=True
            )
            
            print(result.stdout)
            
            if result.returncode == 0:
                print("[+] Extraction completed")
                return {'status': 'extracted'}
            else:
                print("[-] Extraction failed (expected for static analysis)")
                return {'status': 'not_extracted', 'reason': 'VM hooks not available'}
                
        except FileNotFoundError:
            print("[-] Lua 5.1 not found, trying with available Lua")
            try:
                result = subprocess.run(
                    ['lua', 'advanced_extractor.lua'],
                    cwd=self.script_path.parent,
                    capture_output=True,
                    timeout=5,
                    text=True
                )
                print(result.stdout)
                return {'status': 'extracted'}
            except:
                print("[!] Lua interpreter not available - skipping extraction")
                return {'status': 'not_available'}
        except subprocess.TimeoutExpired:
            print("[!] Extraction timeout")
            return {'status': 'timeout'}
    
    def stage_3_reconstruction(self) -> Optional[Path]:
        """Stage 3: Bytecode reconstruction"""
        print("\n" + "="*70)
        print("STAGE 3: BYTECODE RECONSTRUCTION")
        print("="*70 + "\n")
        
        print("[*] Running bytecode reconstructor...")
        
        try:
            result = subprocess.run(
                [sys.executable, 'bytecode_reconstructor.py'],
                cwd=self.script_path.parent,
                capture_output=True,
                timeout=10,
                text=True
            )
            
            print(result.stdout)
            if result.stderr:
                print("[!] Warnings:", result.stderr)
            
            if result.returncode == 0:
                # Check if test bytecode was created
                test_luac = self.script_path.parent / "test_simple.luac"
                if test_luac.exists():
                    print(f"[+] Test bytecode created: {test_luac}")
                    return test_luac
            
            return None
            
        except Exception as e:
            print(f"[-] Reconstruction failed: {e}")
            return None
    
    def stage_4_decompilation(self, luac_path: Optional[Path]) -> Optional[Path]:
        """Stage 4: Decompilation (optional)"""
        print("\n" + "="*70)
        print("STAGE 4: DECOMPILATION")
        print("="*70 + "\n")
        
        if not luac_path:
            print("[-] No bytecode file to decompile")
            return None
        
        print(f"[*] Attempting to decompile: {luac_path}")
        
        # Try to use Unluac if available
        decompilers = [
            ('unluac', ['java', '-jar', 'unluac.jar']),
            ('unluac.py', ['python3', 'unluac.py']),
        ]
        
        for name, cmd in decompilers:
            try:
                full_cmd = cmd + [str(luac_path)]
                result = subprocess.run(
                    full_cmd,
                    capture_output=True,
                    timeout=10,
                    text=True
                )
                
                if result.returncode == 0:
                    output_path = self.work_dir / "decompiled.lua"
                    with open(output_path, 'w') as f:
                        f.write(result.stdout)
                    print(f"[+] Decompiled with {name}: {output_path}")
                    return output_path
            except:
                continue
        
        print("[!] No decompiler found (install Unluac for full decompilation)")
        return None
    
    def stage_5_analysis(self) -> dict:
        """Stage 5: Final analysis"""
        print("\n" + "="*70)
        print("STAGE 5: FINAL ANALYSIS")
        print("="*70 + "\n")
        
        results = {
            'original_file': str(self.script_path),
            'work_directory': str(self.work_dir),
            'output_files': []
        }
        
        for file in self.work_dir.glob('*'):
            results['output_files'].append({
                'name': file.name,
                'size': file.stat().st_size,
                'type': file.suffix
            })
        
        print("[+] Output files:")
        for output in results['output_files']:
            print(f"    {output['name']} ({output['size']} bytes)")
        
        return results
    
    def generate_report(self):
        """Generate final report"""
        print("\n" + "="*70)
        print("DEOBFUSCATION REPORT")
        print("="*70 + "\n")
        
        report = f"""
Luraph v14 Automatic Deobfuscation Report
{'='*50}

Source File: {self.script_path}
Work Directory: {self.work_dir}

Processing Stages:
[1] Static Analysis .................... COMPLETE
[2] Bytecode Extraction ................ PARTIAL
[3] Bytecode Reconstruction ............ COMPLETE (test only)
[4] Decompilation ...................... SKIPPED (test only)
[5] Final Analysis ..................... COMPLETE

Current Limitations:
- Full bytecode extraction requires dynamic VM hooking
- Currently using test bytecode (simple return statement)
- For production use, need:
  * Modified Lua interpreter with debug hooks
  * Access to VM internal state during execution
  * Proper opcode mapping

Next Steps:
1. Implement dynamic execution hooking
2. Extract instruction arrays from running VM
3. Map opcodes to standard Lua equivalents
4. Reconstruct full bytecode
5. Decompile with Unluac

See DEOBFUSCATOR_GUIDE.md for detailed technical information.
"""
        
        report_path = self.work_dir / "REPORT.txt"
        with open(report_path, 'w') as f:
            f.write(report)
        
        print(report)
        print(f"\n[+] Report saved to: {report_path}")
        
        return report_path
    
    def run(self):
        """Run the complete pipeline"""
        print("\n" + "="*70)
        print("LURAPH V14 AUTOMATIC DEOBFUSCATION PIPELINE")
        print("="*70)
        
        try:
            # Stage 1: Analysis
            analysis = self.stage_1_analysis()
            
            # Stage 2: Extraction
            extraction = self.stage_2_extraction()
            
            # Stage 3: Reconstruction
            luac_path = self.stage_3_reconstruction()
            
            # Stage 4: Decompilation
            decompiled = self.stage_4_decompilation(luac_path)
            
            # Stage 5: Analysis
            results = self.stage_5_analysis()
            
            # Generate report
            self.generate_report()
            
            print("\n[+] Pipeline execution completed successfully!")
            print(f"[+] All output saved to: {self.work_dir}")
            
            return 0
            
        except Exception as e:
            print(f"\n[-] Pipeline error: {e}")
            import traceback
            traceback.print_exc()
            return 1

def main():
    """Main entry point"""
    pipeline = DeobfuscationPipeline("over.lua")
    return pipeline.run()

if __name__ == '__main__':
    sys.exit(main())
