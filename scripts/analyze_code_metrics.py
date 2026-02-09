#!/usr/bin/env python3
"""
Code analysis tool to monitor refactoring progress.
Tracks file sizes, complexity, and refactoring metrics.
"""

import ast
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple
import json
from datetime import datetime


class CodeAnalyzer:
    """Analyzes code metrics for refactoring monitoring."""
    
    def __init__(self, src_dir: str = "src"):
        self.src_dir = Path(src_dir)
        self.metrics = {}
        
    def analyze_file(self, file_path: Path) -> Dict:
        """Analyze a single Python file for metrics."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            tree = ast.parse(content)
            
            metrics = {
                'file_path': str(file_path),
                'line_count': len(content.splitlines()),
                'function_count': len([n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]),
                'class_count': len([n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]),
                'complexity_score': self._calculate_complexity(tree),
                'import_count': len([n for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))]),
            }
            
            return metrics
            
        except Exception as e:
            return {
                'file_path': str(file_path),
                'error': str(e),
                'line_count': 0,
                'function_count': 0,
                'class_count': 0,
                'complexity_score': 0,
                'import_count': 0,
            }
    
    def _calculate_complexity(self, tree: ast.AST) -> int:
        """Calculate cyclomatic complexity score."""
        complexity = 1  # Base complexity
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(node, ast.ExceptHandler):
                complexity += 1
            elif isinstance(node, (ast.And, ast.Or)):
                complexity += 1
                
        return complexity
    
    def analyze_directory(self) -> Dict:
        """Analyze all Python files in the source directory."""
        results = {
            'timestamp': datetime.now().isoformat(),
            'files': [],
            'summary': {
                'total_files': 0,
                'total_lines': 0,
                'large_files': [],  # >1000 lines
                'critical_files': [],  # >2000 lines
                'medium_files': [],  # 500-1000 lines
            }
        }
        
        for py_file in self.src_dir.rglob("*.py"):
            if py_file.name.startswith('__'):
                continue
                
            metrics = self.analyze_file(py_file)
            results['files'].append(metrics)
            
            # Update summary
            results['summary']['total_files'] += 1
            results['summary']['total_lines'] += metrics['line_count']
            
            # Categorize files by size
            if metrics['line_count'] > 2000:
                results['summary']['critical_files'].append({
                    'file': str(py_file),
                    'lines': metrics['line_count'],
                    'functions': metrics['function_count']
                })
            elif metrics['line_count'] > 1000:
                results['summary']['large_files'].append({
                    'file': str(py_file),
                    'lines': metrics['line_count'],
                    'functions': metrics['function_count']
                })
            elif metrics['line_count'] > 500:
                results['summary']['medium_files'].append({
                    'file': str(py_file),
                    'lines': metrics['line_count'],
                    'functions': metrics['function_count']
                })
        
        return results
    
    def generate_report(self, output_file: str = "code_metrics.json"):
        """Generate and save code metrics report."""
        results = self.analyze_directory()
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        # Print summary to console
        summary = results['summary']
        print(f"Code Analysis Report - {results['timestamp']}")
        print(f"Total files analyzed: {summary['total_files']}")
        print(f"Total lines of code: {summary['total_lines']:,}")
        print(f"Critical files (>2000 lines): {len(summary['critical_files'])}")
        print(f"Large files (1000-2000 lines): {len(summary['large_files'])}")
        print(f"Medium files (500-1000 lines): {len(summary['medium_files'])}")
        
        if summary['critical_files']:
            print("\nCritical files requiring immediate refactoring:")
            for file_info in summary['critical_files']:
                print(f"  - {file_info['file']}: {file_info['lines']} lines, {file_info['functions']} functions")
        
        if summary['large_files']:
            print("\nLarge files for refactoring consideration:")
            for file_info in summary['large_files']:
                print(f"  - {file_info['file']}: {file_info['lines']} lines, {file_info['functions']} functions")
        
        print(f"\nDetailed report saved to: {output_file}")
        return results


def main():
    """Main entry point for code analysis."""
    analyzer = CodeAnalyzer()
    analyzer.generate_report()


if __name__ == "__main__":
    main()