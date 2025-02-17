# Lessons

- For website image paths, always use the correct relative path (e.g., 'images/filename.png') and ensure the images directory exists
- For search results, ensure proper handling of different character encodings (UTF-8) for international queries
- Add debug information to stderr while keeping the main output clean in stdout for better pipeline integration
- When using seaborn styles in matplotlib, use 'seaborn-v0_8' instead of 'seaborn' as the style name due to recent seaborn version changes
- When using Jest, a test suite can fail even if all individual tests pass, typically due to issues in suite-level setup code or lifecycle hooks
- When using Google Gemini API:
  - Use the correct model name format (e.g., 'gemini-1.5-pro', 'gemini-1.5-flash')
  - Require GOOGLE_API_KEY environment variable
  - Use the correct model name format (e.g., 'gemini-2.0-pro-exp-02-05')

# Scratchpad
