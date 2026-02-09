#!/usr/bin/env python3
"""
Refactoring progress tracker.
Monitors the progress of code refactoring tasks.
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List


class RefactoringTracker:
    """Tracks refactoring progress and milestones."""
    
    def __init__(self, progress_file: str = "refactoring_progress.json"):
        self.progress_file = progress_file
        self.progress_data = self._load_progress()
    
    def _load_progress(self) -> Dict:
        """Load existing progress data or create new."""
        if os.path.exists(self.progress_file):
            with open(self.progress_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        return {
            'start_date': datetime.now().isoformat(),
            'milestones': [],
            'refactored_files': [],
            'metrics_history': [],
        }
    
    def add_milestone(self, task: str, description: str, files_affected: List[str] = None):
        """Add a refactoring milestone."""
        milestone = {
            'timestamp': datetime.now().isoformat(),
            'task': task,
            'description': description,
            'files_affected': files_affected or [],
        }
        
        self.progress_data['milestones'].append(milestone)
        self._save_progress()
        
        print(f"Milestone recorded: {task}")
        print(f"   {description}")
        if files_affected:
            print(f"   Files affected: {', '.join(files_affected)}")
    
    def mark_file_refactored(self, original_file: str, new_modules: List[str]):
        """Mark a file as successfully refactored."""
        refactored_entry = {
            'timestamp': datetime.now().isoformat(),
            'original_file': original_file,
            'new_modules': new_modules,
            'status': 'completed'
        }
        
        self.progress_data['refactored_files'].append(refactored_entry)
        self._save_progress()
        
        print(f"File refactored: {original_file}")
        print(f"   Split into: {', '.join(new_modules)}")
    
    def add_metrics_snapshot(self, metrics: Dict):
        """Add a metrics snapshot to track progress."""
        snapshot = {
            'timestamp': datetime.now().isoformat(),
            'metrics': metrics
        }
        
        self.progress_data['metrics_history'].append(snapshot)
        self._save_progress()
    
    def _save_progress(self):
        """Save progress data to file."""
        with open(self.progress_file, 'w', encoding='utf-8') as f:
            json.dump(self.progress_data, f, indent=2, ensure_ascii=False)
    
    def generate_progress_report(self):
        """Generate a progress report."""
        print("Refactoring Progress Report")
        print("=" * 50)
        
        start_date = datetime.fromisoformat(self.progress_data['start_date'])
        print(f"Started: {start_date.strftime('%Y-%m-%d %H:%M')}")
        
        milestones = self.progress_data['milestones']
        print(f" Milestones completed: {len(milestones)}")
        
        refactored = self.progress_data['refactored_files']
        print(f"Files refactored: {len(refactored)}")
        
        if milestones:
            print("\nRecent milestones:")
            for milestone in milestones[-5:]:  # Show last 5
                timestamp = datetime.fromisoformat(milestone['timestamp'])
                print(f"  • {timestamp.strftime('%m-%d %H:%M')} - {milestone['task']}")
        
        if refactored:
            print("\nRefactored files:")
            for entry in refactored:
                print(f"  • {entry['original_file']} → {len(entry['new_modules'])} modules")


def main():
    """Main entry point for progress tracking."""
    tracker = RefactoringTracker()
    
    if len(os.sys.argv) > 1:
        command = os.sys.argv[1]
        
        if command == "milestone" and len(os.sys.argv) >= 4:
            task = os.sys.argv[2]
            description = os.sys.argv[3]
            files = os.sys.argv[4:] if len(os.sys.argv) > 4 else []
            tracker.add_milestone(task, description, files)
        
        elif command == "refactored" and len(os.sys.argv) >= 4:
            original = os.sys.argv[2]
            modules = os.sys.argv[3:]
            tracker.mark_file_refactored(original, modules)
        
        elif command == "report":
            tracker.generate_progress_report()
        
        else:
            print("Usage:")
            print("  python refactoring_progress.py milestone <task> <description> [files...]")
            print("  python refactoring_progress.py refactored <original_file> <module1> [module2...]")
            print("  python refactoring_progress.py report")
    
    else:
        tracker.generate_progress_report()


if __name__ == "__main__":
    main()