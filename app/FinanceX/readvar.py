# Define the name of your configuration file
config_file_path = './resources/variables.txt'

# Create a dictionary to hold the key-value pairs
config_dict = {}

# Open and read the file
with open(config_file_path, 'r') as file:
    for line in file:
        # Strip any trailing whitespace (including newlines) and skip blank lines
        line = line.strip()
        if not line:
            continue
        
        # Split each line on the '=' character
        if '=' in line:
            key, value = line.split('=', 1)
            config_dict[key.strip()] = value.strip()

# Optionally, load them as variables (can be accessed dynamically)
for key, value in config_dict.items():
    globals()[value] = key
