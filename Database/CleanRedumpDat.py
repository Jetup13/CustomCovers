import os
import re

# Function to extract <description> tags, replace &amp; with &, and alphabetize them
def clean_dat_file(dat_file):
    descriptions = []
    
    # Read the .dat file
    with open(dat_file, 'r', encoding='utf-8') as file:
        content = file.read()
        
        # Extract all descriptions
        descriptions = re.findall(r'<description>(.*?)</description>', content)
        
        # Replace &amp; with &
        descriptions = [desc.replace('&amp;', '&') for desc in descriptions]
        
    # Sort descriptions alphabetically
    descriptions.sort()

    # Output to a .txt file with the same name as the .dat file
    txt_file = os.path.splitext(dat_file)[0] + '.txt'
    with open(txt_file, 'w', encoding='utf-8') as file:
        for desc in descriptions:
            file.write(desc + '\n')

# Get all .dat files in the current folder
dat_files = [file for file in os.listdir() if file.endswith('.dat')]

# Process each .dat file
for dat_file in dat_files:
    clean_dat_file(dat_file)

print("Descriptions extracted, &amp; replaced, and sorted into .txt files.")
