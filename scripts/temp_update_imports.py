import os

def update_imports():
    for root, _, files in os.walk('app'):
        for f in files:
            if not f.endswith('.py'):
                continue
            
            p = os.path.join(root, f)
            with open(p, 'r', encoding='utf-8') as file:
                content = file.read()
                
            if 'academics_service' in content or 'academics_schemas' in content:
                print(f"Updating: {p}")
                # Replace forms that alias it as acad_srv
                content = content.replace(
                    'from app.modules.academics import academics_service as acad_srv',
                    'import app.modules.academics as acad_srv'
                )
                # Replace specific imports from the file
                content = content.replace(
                    'from app.modules.academics.academics_service import',
                    'from app.modules.academics import'
                )
                # Replace direct imports of the file named academics_service
                content = content.replace(
                    'from app.modules.academics import academics_service',
                    'import app.modules.academics as academics_service'
                )
                content = content.replace(
                    'import app.modules.academics.academics_service as acad_srv',
                    'import app.modules.academics as acad_srv'
                )
                # Replace old schemas legacy file
                content = content.replace(
                    'from app.modules.academics.academics_schemas import',
                    'from app.modules.academics.schemas import'
                )
                
                with open(p, 'w', encoding='utf-8') as file:
                    file.write(content)

if __name__ == '__main__':
    update_imports()
