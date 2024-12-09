Please follow these instructions in everything you do:
1. DO NOT REMOVE FUNCTIONALITY UNLESS EXPLICITLY REQUESTED.
2. Do not install Python packages via code; just inform me to run pip.
3. DO NOT REMOVE COMMENTS unless explicitly requested.
4. Always add a #!/usr/bin/env python3 at the top of the file.
5. Include import statements at the top of the file.

Conventions:
------------
1. Use snake_case for variable and function names.
2. Use UPPERCASE for constants.
3. Use PascalCase for class names.
4. Use spaces around operators and after commas.
5. Use 4 spaces for indentation (no tabs).
6. Keep lines to a maximum of 79 characters.
7. Use descriptive variable names.
8. Add docstrings to all functions, classes, and modules.
9. Use type hints for function arguments and return values.
10. Use 'is' or 'is not' for comparisons to None, True, or False.
11. Use context managers (with statements) when dealing with resources.
12. Follow PEP 8 style guide for Python code.
13. Organize imports into three groups: standard library imports, third-party imports, and local application imports, separated by a blank line.
14. Avoid wildcard imports (e.g., from module_name import *).
15. Use list comprehensions and generator expressions where appropriate for readability and efficiency.
16. Use f-strings for formatting strings (Python 3.6+).
17. Handle exceptions using try/except blocks and avoid using bare except clauses (always specify the exception type).
18. Avoid mutable default arguments in function definitions (e.g., use None and check inside the function).
19. Ensure that each Python file ends with a newline.
20. Use the built-in logging module for logging rather than print statements for debugging.
21. Avoid deep nesting of code blocks to maintain readability (e.g., by returning early from a function).
22. Use the __name__ == '__main__' guard to ensure that code only runs when the script is executed directly, not when it is imported as a module.
23. Comment your code where necessary to explain the why behind non-obvious decisions or algorithms.
24. Regularly refactor your code to improve readability, maintainability, and performance.
25. Write unit tests to verify the correctness of your code and follow Test-Driven Development (TDD) principles where applicable.
