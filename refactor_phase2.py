import os

def rename_entities(root_dir):
    # Step 1: Content replacements
    print("Starting content replacement...")
    for dirpath, _, filenames in os.walk(root_dir):
        if '.git' in dirpath or '.venv' in dirpath:
            continue
        for fname in filenames:
            if fname.endswith(('.py', '.sql', '.md')):
                path = os.path.join(dirpath, fname)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                except: continue
                
                # Careful replacements to maintain case
                # The word "Parent" -> "Parent"
                new_content = content.replace('Parent', 'Parent')
                new_content = new_content.replace('parent', 'parent')
                new_content = new_content.replace('PARENT', 'PARENT')
                
                if new_content != content:
                    with open(path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    print(f"Updated content inside: {path}")

    # Step 2: File and Folder Renames
    print("\nStarting file and directory renames...")
    for dirpath, dirnames, filenames in os.walk(root_dir, topdown=False):
        if '.git' in dirpath or '.venv' in dirpath:
            continue
            
        for fname in filenames:
            if 'parent' in fname.lower():
                new_fname = fname.replace('parent', 'parent').replace('Parent', 'Parent')
                old_path = os.path.join(dirpath, fname)
                new_path = os.path.join(dirpath, new_fname)
                os.rename(old_path, new_path)
                print(f"Renamed file: {old_path} -> {new_path}")
                
        for dname in dirnames:
            if 'parent' in dname.lower():
                new_dname = dname.replace('parent', 'parent').replace('Parent', 'Parent')
                old_path = os.path.join(dirpath, dname)
                new_path = os.path.join(dirpath, new_dname)
                os.rename(old_path, new_path)
                print(f"Renamed directory: {old_path} -> {new_path}")

if __name__ == "__main__":
    rename_entities('.')
