import os

folder_path = "data/workspaces/modified"

# Create the folder and any necessary parent directories if they don't exist
os.makedirs(folder_path, exist_ok=True)

print(f"Directory '{folder_path}' ensured to exist.")