import os
import ast

def extract_features(directory="src"):
    features = []

    features.append("# Core System Overview")
    features.append("The repository represents HANERMA APEX, a state-of-the-art AI multi-agent orchestration framework.")
    features.append("It achieves high-performance parallelism through Abstract Syntax Tree (AST) analysis, dynamic memory compression (HCMS/Xerv-Crayon), deterministic logical reasoning (via Z3), and a real-time reactive execution graph.")
    features.append("")
    features.append("# Detailed Architectural Features & Capabilities")

    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                path = os.path.join(root, file)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        content = f.read()
                        tree = ast.parse(content)
                        module_doc = ast.get_docstring(tree)

                        file_added = False

                        def add_file_header():
                            nonlocal file_added
                            if not file_added:
                                features.append(f"\n## Module: `{path}`")
                                if module_doc:
                                    features.append(f"  *Description:* {module_doc.split(chr(10))[0]}")
                                file_added = True

                        for node in ast.walk(tree):
                            if isinstance(node, ast.ClassDef):
                                add_file_header()
                                class_doc = ast.get_docstring(node)
                                doc_str = f" - {class_doc.split(chr(10))[0]}" if class_doc else ""
                                features.append(f"- **Class: `{node.name}`**{doc_str}")

                                for item in node.body:
                                    if isinstance(item, ast.FunctionDef) and not item.name.startswith("_"):
                                        method_doc = ast.get_docstring(item)
                                        m_doc_str = f": {method_doc.split(chr(10))[0]}" if method_doc else ""
                                        features.append(f"  - **Method `{item.name}`**{m_doc_str}")

                            elif isinstance(node, ast.FunctionDef) and not node.name.startswith("_"):
                                # Ensure we don't grab methods again
                                is_method = False
                                for parent in ast.walk(tree):
                                    if isinstance(parent, ast.ClassDef):
                                        if node in parent.body:
                                            is_method = True
                                            break
                                if not is_method:
                                    add_file_header()
                                    func_doc = ast.get_docstring(node)
                                    f_doc_str = f": {func_doc.split(chr(10))[0]}" if func_doc else ""
                                    features.append(f"- **Function `{node.name}`**{f_doc_str}")
                except Exception as e:
                    features.append(f"Error parsing {path}: {e}")
    return "\n".join(features)

if __name__ == "__main__":
    markdown = extract_features()
    with open("ALL_FEATURES_HYPERDETAILED.md", "w", encoding="utf-8") as f:
        f.write(markdown)
    print("Created ALL_FEATURES_HYPERDETAILED.md")
