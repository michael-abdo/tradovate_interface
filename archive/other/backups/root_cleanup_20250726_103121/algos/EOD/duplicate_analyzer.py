#!/usr/bin/env python3
"""
Duplicate Code Analyzer - Identifies semantic duplicates across the codebase
"""

import os
import ast
import hashlib
import json
from typing import Dict, List, Set, Tuple
from collections import defaultdict
from dataclasses import dataclass, field

@dataclass
class FunctionSignature:
    name: str
    file_path: str
    line_start: int
    line_end: int
    args: List[str]
    returns: str
    body_hash: str
    calls: Set[str] = field(default_factory=set)
    imports: Set[str] = field(default_factory=set)
    
    def semantic_key(self) -> str:
        """Generate a key based on semantic behavior"""
        return f"{sorted(self.args)}:{self.returns}:{self.body_hash}"

class DuplicateAnalyzer:
    def __init__(self, root_dir: str):
        self.root_dir = root_dir
        self.functions: Dict[str, List[FunctionSignature]] = defaultdict(list)
        self.semantic_groups: Dict[str, List[FunctionSignature]] = defaultdict(list)
        
    def analyze_file(self, file_path: str):
        """Analyze a Python file for functions"""
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    sig = self._extract_signature(node, file_path, content)
                    self.functions[sig.name].append(sig)
                    
        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")
    
    def _extract_signature(self, node: ast.FunctionDef, file_path: str, content: str) -> FunctionSignature:
        """Extract function signature and semantic information"""
        # Get function arguments
        args = [arg.arg for arg in node.args.args]
        
        # Get return type if specified
        returns = ast.unparse(node.returns) if node.returns else "None"
        
        # Hash the function body (excluding decorators and docstrings)
        body_nodes = []
        for child in node.body:
            if not (isinstance(child, ast.Expr) and isinstance(child.value, ast.Str)):
                body_nodes.append(ast.unparse(child))
        
        body_str = '\n'.join(body_nodes)
        body_hash = hashlib.md5(body_str.encode()).hexdigest()[:8]
        
        # Extract function calls
        calls = set()
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Name):
                    calls.add(child.func.id)
                elif isinstance(child.func, ast.Attribute):
                    calls.add(f"{ast.unparse(child.func.value)}.{child.func.attr}")
        
        return FunctionSignature(
            name=node.name,
            file_path=file_path,
            line_start=node.lineno,
            line_end=node.end_lineno or node.lineno,
            args=args,
            returns=returns,
            body_hash=body_hash,
            calls=calls
        )
    
    def find_semantic_duplicates(self):
        """Group functions by semantic similarity"""
        # Group by semantic key
        for func_list in self.functions.values():
            for func in func_list:
                key = func.semantic_key()
                self.semantic_groups[key].append(func)
        
        # Find groups with duplicates
        duplicates = {}
        for key, group in self.semantic_groups.items():
            if len(group) > 1:
                duplicates[key] = group
        
        return duplicates
    
    def find_near_duplicates(self, threshold: float = 0.8):
        """Find functions that are similar but not exact duplicates"""
        near_duplicates = []
        
        func_list = []
        for funcs in self.functions.values():
            func_list.extend(funcs)
        
        for i, func1 in enumerate(func_list):
            for func2 in func_list[i+1:]:
                similarity = self._calculate_similarity(func1, func2)
                if similarity >= threshold and similarity < 1.0:
                    near_duplicates.append((func1, func2, similarity))
        
        return near_duplicates
    
    def _calculate_similarity(self, func1: FunctionSignature, func2: FunctionSignature) -> float:
        """Calculate similarity between two functions"""
        scores = []
        
        # Name similarity (excluding exact matches)
        if func1.name == func2.name:
            scores.append(1.0)
        elif func1.name.lower() == func2.name.lower():
            scores.append(0.9)
        elif func1.name.replace('_', '') == func2.name.replace('_', ''):
            scores.append(0.8)
        else:
            scores.append(0.0)
        
        # Argument similarity
        args1 = set(func1.args)
        args2 = set(func2.args)
        if args1 and args2:
            arg_similarity = len(args1 & args2) / max(len(args1), len(args2))
            scores.append(arg_similarity)
        
        # Call similarity
        calls1 = func1.calls
        calls2 = func2.calls
        if calls1 and calls2:
            call_similarity = len(calls1 & calls2) / max(len(calls1), len(calls2))
            scores.append(call_similarity)
        
        # Body hash similarity
        if func1.body_hash == func2.body_hash:
            scores.append(1.0)
        else:
            scores.append(0.0)
        
        return sum(scores) / len(scores) if scores else 0.0
    
    def analyze_directory(self, directory: str):
        """Recursively analyze all Python files in directory"""
        for root, dirs, files in os.walk(directory):
            # Skip __pycache__ and .git directories
            dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', 'node_modules']]
            
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    self.analyze_file(file_path)

def main():
    analyzer = DuplicateAnalyzer('.')
    
    print("🔍 Analyzing codebase for duplicates...")
    analyzer.analyze_directory('./tasks')
    
    # Find exact semantic duplicates
    print("\n📊 EXACT SEMANTIC DUPLICATES:")
    print("=" * 80)
    
    duplicates = analyzer.find_semantic_duplicates()
    for key, group in duplicates.items():
        print(f"\nDuplicate group ({len(group)} instances):")
        for func in group:
            rel_path = os.path.relpath(func.file_path, '.')
            print(f"  - {func.name} in {rel_path}:{func.line_start}-{func.line_end}")
            print(f"    Args: {func.args}, Returns: {func.returns}")
    
    # Find near duplicates
    print("\n🔎 NEAR DUPLICATES (>80% similar):")
    print("=" * 80)
    
    near_dupes = analyzer.find_near_duplicates(threshold=0.8)
    for func1, func2, similarity in sorted(near_dupes, key=lambda x: x[2], reverse=True):
        rel_path1 = os.path.relpath(func1.file_path, '.')
        rel_path2 = os.path.relpath(func2.file_path, '.')
        print(f"\n{similarity:.0%} similar:")
        print(f"  1. {func1.name} in {rel_path1}:{func1.line_start}")
        print(f"  2. {func2.name} in {rel_path2}:{func2.line_start}")
        print(f"  Common calls: {func1.calls & func2.calls}")
    
    # Save results for further analysis
    results = {
        'exact_duplicates': {
            key: [{'name': f.name, 'file': f.file_path, 'line': f.line_start} 
                  for f in group]
            for key, group in duplicates.items()
        },
        'near_duplicates': [
            {
                'similarity': similarity,
                'func1': {'name': func1.name, 'file': func1.file_path, 'line': func1.line_start},
                'func2': {'name': func2.name, 'file': func2.file_path, 'line': func2.line_start}
            }
            for func1, func2, similarity in near_dupes
        ]
    }
    
    with open('duplicate_analysis.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📁 Results saved to duplicate_analysis.json")
    print(f"📈 Total functions analyzed: {sum(len(funcs) for funcs in analyzer.functions.values())}")
    print(f"⚠️  Exact duplicate groups: {len(duplicates)}")
    print(f"🔍 Near duplicate pairs: {len(near_dupes)}")

if __name__ == '__main__':
    main()