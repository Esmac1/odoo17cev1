#!/usr/bin/env python3
import os
import re
import ast

def check_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Use AST to find class definitions
    tree = ast.parse(content)
    
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            # Check if class inherits from models.Model
            for base in node.bases:
                if (isinstance(base, ast.Attribute) and base.attr == 'Model' and 
                    isinstance(base.value, ast.Name) and base.value.id == 'models'):
                    # Check for _description attribute
                    has_desc = False
                    for subnode in node.body:
                        if isinstance(subnode, ast.Assign):
                            for target in subnode.targets:
                                if isinstance(target, ast.Name) and target.id == '_description':
                                    has_desc = True
                                    break
                    
                    if not has_desc:
                        print(f"❌ {os.path.basename(filepath)}: Class '{node.name}' missing _description")
                    else:
                        print(f"✅ {os.path.basename(filepath)}: Class '{node.name}' has _description")

# Check all Python files
for filename in os.listdir('.'):
    if filename.endswith('.py') and filename != '__init__.py' and filename != 'check_descriptions.py':
        check_file(filename)
