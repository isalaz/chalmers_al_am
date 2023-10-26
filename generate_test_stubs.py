import os
import importlib
import inspect

src_directory = "src"  # Change this to the path of your src directory
tests_directory = "tests"  # Change this to the path of your tests directory
test_functions_added = 0
# Recursively search for .py files in the src directory
for root, _, files in os.walk(src_directory):
    for file in files:
        if file.endswith(".py"):
            # Create the corresponding directory structure in tests
            if "__init__" in file:
                continue
            
            relative_path = os.path.relpath(root, src_directory)
           
            if relative_path == '.':
                relative_path = ''
            
            tests_dir_path = os.path.join(tests_directory, relative_path)
            
          
            # Create the tests directory if it doesn't exist
            os.makedirs(tests_dir_path, exist_ok=True)

            # Generate the test script filename (e.g., "module.py" -> "test_module.py")
            module_name, _ = os.path.splitext(file)
            test_script_name = f"test_{module_name}.py"
            test_script_path = os.path.join(tests_dir_path, test_script_name)
            
            # Check if the test script already exists
            if os.path.exists(test_script_path):
                with open(test_script_path, "r") as existing_test_script:
                    existing_content = existing_test_script.read()

                with open(test_script_path, "a") as test_script:
                    # Import the source module
                    # Adjusted import statement with the 'package' parameter
                    
                    source_module = importlib.import_module(f"{root.replace(os.path.sep, '.')}.{module_name}", package='src')


                    # Get all function names from the source module
                    functions = [name for name, _ in inspect.getmembers(source_module, inspect.isfunction)]

                    # Append new test function stubs
                    for function_name in functions:
                        if f"test_{function_name}()" not in existing_content:
                            print(f'Creating {function_name} in {test_script_path}')
                            test_script.write(f"\n# Test function for {function_name}\n")
                            test_script.write(f"def test_{function_name}():\n")
                            test_script.write(f"    # Your test code here\n")
                            test_script.write(f"    pass\n")
                            test_functions_added += 1

            else:
                with open(test_script_path, "w") as test_script:
                    # Import the source module
                    # Adjusted import statement with the 'package' parameter
                    source_module = importlib.import_module(f"{root.replace(os.path.sep, '.')}.{module_name}", package='src')


                    # Get all function names from the source module
                    functions = [name for name, _ in inspect.getmembers(source_module, inspect.isfunction)]

                    # Generate the entire test script
                    test_script.write(f"import {module_name}\n\n")

                    for function_name in functions:
                        print(f'Creating test_{function_name} in {test_script_path}')
                        test_script.write(f"# Test function for {function_name}\n")
                        test_script.write(f"def test_{function_name}():\n")
                        test_script.write(f"    # Your test code here\n")
                        test_script.write(f"    pass\n")
                        test_functions_added += 1

print(f"{test_functions_added} new test functions added")
