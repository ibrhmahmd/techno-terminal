import os

def replace_in_files(root_dir):
    for dirpath, _, filenames in os.walk(root_dir):
        if '.git' in dirpath or '.venv' in dirpath: continue
        for fname in filenames:
            if fname.endswith(('.py', '.md')):
                path = os.path.join(dirpath, fname)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                except: continue
                
                new_content = content.replace('Techno Terminal', 'Techno Terminal').replace('Techno Terminal', 'Techno Terminal')
                new_content = new_content.replace('f"Session {', 'f"Session {')
                
                if new_content != content:
                    with open(path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    print('Updated', path)

replace_in_files('.')
