import json
import os
from datetime import date


def split_workspaces_into_chunks(input_file_path, output_dir, chunk_size=500):
    """
    Split a JSON file containing workspace IDs into smaller chunks.
    
    Args:
        input_file_path (str): Path to the input JSON file
        output_dir (str): Directory where chunk files will be saved
        chunk_size (int): Number of IDs per chunk (default: 500)
    
    Returns:
        int: Number of chunk files created
    """
    # Read the input JSON file
    with open(input_file_path, 'r', encoding='utf-8') as f:
        workspaces = json.load(f)
    
    total_workspaces = len(workspaces)
    print(f"Total workspaces found: {total_workspaces}")
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Split into chunks and save
    chunk_count = 0
    for i in range(0, total_workspaces, chunk_size):
        chunk = workspaces[i:i + chunk_size]
        chunk_count += 1
        
        # Create output filename
        output_file = os.path.join(output_dir, f"workspaces_chunk_{chunk_count}.json")
        
        # Save chunk to file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(chunk, f, indent=4)
        
        print(f"Created {output_file} with {len(chunk)} workspaces")
    
    print(f"\nTotal chunks created: {chunk_count}")
    return chunk_count


def main():
    # Get today's date for the file name
    current_date = date.today().strftime("%Y_%m_%d")
    
    # Define paths
    input_file = f"./data/workspaces/modified/workspaces_{current_date}.json"
    output_directory = f"./data/workspaces/modified/chunks/{current_date}"
    
    # Check if input file exists
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' not found!")
        return
    
    # Split the workspaces into chunks
    split_workspaces_into_chunks(
        input_file_path=input_file,
        output_dir=output_directory,
        chunk_size=500
    )


if __name__ == "__main__":
    main()
