import json

def generate_markdown(openapi_path, output_path):
    with open(openapi_path, 'r', encoding='utf-8') as f:
        spec = json.load(f)

    md = [
        "# Techno Terminal - Frontend API Reference (Full API Map)\n",
        "This document automatically maps all endpoints listed in the OpenAPI specification.\n",
        "---\n\n"
    ]
    
    # Global note about Auth
    md.extend([
        "## 🔐 Global Authentication\n",
        "Most API requests MUST include a Bearer token in the `Authorization` header.\n",
        "```http\nAuthorization: Bearer <access_token>\n```\n\n",
        "---\n\n"
    ])

    paths = spec.get("paths", {})
    mapped_endpoints = []

    # Iterate and group by Tags (or first tag)
    tag_groups = {}
    for path, path_item in paths.items():
        for method, operation in path_item.items():
            tags = operation.get('tags', ['Other'])
            first_tag = tags[0]
            if first_tag not in tag_groups:
                tag_groups[first_tag] = []
            
            tag_groups[first_tag].append({
                "path": path,
                "method": method.upper(),
                "operation": operation
            })

    # Generate sections based on tags
    for tag_name, endpoints in sorted(tag_groups.items()):
        md.append(f"## {tag_name}\n\n")
        for ep in endpoints:
            op = ep['operation']
            path = ep['path']
            method = ep['method']
            
            summary = op.get('summary', '')
            md.append(f"### {summary} ([{method}] {path})\n")
            md.append(f"**Method**: `{method}`  \n**Endpoint**: `{path}`  \n")
            
            # Request params
            if 'parameters' in op:
                md.append("**Parameters**:\n")
                for p in op['parameters']:
                    req_mark = "(required)" if p.get('required') else "(optional)"
                    schema_type = p.get('schema', {}).get('type', 'string')
                    md.append(f"- `{p['name']}` a {schema_type} in {p['in']} {req_mark}\n")
                md.append("\n")
                
            # Request body
            if 'requestBody' in op:
                try:
                    schema_ref = op['requestBody']['content']['application/json']['schema'].get('$ref', 'Custom Payload')
                    md.append(f"**Request Body** (JSON): `{schema_ref.split('/')[-1]}`  \n\n")
                except KeyError:
                    pass
            
            # Responses
            if 'responses' in op:
                md.append("**Responses**:\n")
                for code, resp in op['responses'].items():
                    schema_name = "Unknown"
                    try:
                        if 'content' in resp and 'application/json' in resp['content']:
                            schema = resp['content']['application/json'].get('schema', {})
                            if '$ref' in schema:
                                schema_name = schema['$ref'].split('/')[-1]
                            elif 'type' in schema:
                                schema_name = schema['type']
                    except Exception:
                        pass
                    desc = resp.get('description', '')
                    md.append(f"- `{code}`: {desc} (Schema: `{schema_name}`)\n")
            
            md.append("\n---\n\n")

    with open(output_path, 'w', encoding='utf-8') as out_f:
        out_f.write("".join(md))

if __name__ == "__main__":
    generate_markdown('openapi.json', r'docs\product\frontend_api_reference.md')
    print("Documentation generalized and generated successfully!")
