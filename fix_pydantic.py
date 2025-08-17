"""
Quick fix for Pydantic v2 compatibility
"""

import re

def fix_pydantic_v2(file_path):
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Fix regex= to pattern=
    content = content.replace('regex=', 'pattern=')
    
    # Fix @validator to @field_validator with @classmethod
    content = re.sub(
        r'@validator\(([^)]+)\)\s*def (\w+)\(cls,',
        r'@field_validator(\1)\n    @classmethod\n    def \2(cls,',
        content
    )
    
    with open(file_path, 'w') as f:
        f.write(content)

if __name__ == "__main__":
    fix_pydantic_v2("c:/Users/Swanand/CascadeProjects/Petty/src/common/security/output_schemas.py")
    print("Fixed output_schemas.py for Pydantic v2 compatibility")
