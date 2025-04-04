import os
import zipfile

def zip_output_directory(output_dir, zip_file_name):
    with zipfile.ZipFile(zip_file_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(output_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, output_dir)
                zipf.write(file_path, arcname)

if __name__ == "__main__":
    output_directory = "output"  # Replace with your output directory path
    zip_file_name = "output/test.sb3"  # Replace with your desired zip file name
    zip_output_directory(output_directory, zip_file_name)
    print(f"All files in '{output_directory}' have been zipped into '{zip_file_name}'.")