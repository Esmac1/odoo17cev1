#!/usr/bin/env python3
import os
import re

def check_field_references():
    models_dir = 'models'
    issues = []
    
    # Field names in account model
    account_fields = {'name', 'code', 'type', 'parent_id', 'currency_id', 
                     'company_id', 'active', 'balance', 'complete_name'}
    
    for filename in os.listdir(models_dir):
        if filename.endswith('.py'):
            filepath = os.path.join(models_dir, filename)
            with open(filepath, 'r') as f:
                content = f.read()
                
            # Check for references to account fields that don't exist
            matches = re.findall(r"account_id\.(\w+)", content)
            for match in matches:
                if match not in account_fields and match != 'id':
                    issues.append(f"{filename}: references account_id.{match} which doesn't exist")
    
    return issues

if __name__ == '__main__':
    issues = check_field_references()
    if issues:
        print("Found issues:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("✅ All field references are valid!")
