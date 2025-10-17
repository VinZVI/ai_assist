import re
import subprocess

# Run ruff check and get output
result = subprocess.run(
    ["ruff", "check", "--output-format=concise"],
    capture_output=True,
    text=True,
    cwd="c:\\Users\\User\\PycharmProjects\\ai_assist",
)

# Parse errors
errors = result.stdout.splitlines()
error_types = {}

for error in errors:
    # Extract error code (e.g., F401, E501, etc.)
    match = re.search(r": ([A-Z]+[0-9]+)", error)
    if match:
        error_code = match.group(1)
        error_types[error_code] = error_types.get(error_code, 0) + 1

# Print summary
print("Error types summary:")
for error_code, count in sorted(error_types.items()):
    print(f"{error_code}: {count}")

print(f"\nTotal errors: {len(errors)}")
