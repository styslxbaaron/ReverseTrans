from flask import Flask, request, render_template, send_from_directory
import json
import re
from collections import OrderedDict
import io
import os

app = Flask(__name__)
GENERATED_FILES_DIR = 'generated_files'

# Ensure the directory exists
os.makedirs(GENERATED_FILES_DIR, exist_ok=True)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        data = request.form['data']
        
        # Initialize a dictionary to store the results
        result = {"triplet": {}}

        # Extract species name
        species_pattern = re.compile(r"^(.*?):")
        species_match = species_pattern.match(data.splitlines()[0].strip())
        species_name = "unknown_species"
        if species_match:
            species_name = species_match.group(1).replace(" ", "_")
        
        # Regular expression to extract relevant fields from the entire data block
        pattern = re.compile(r"([AUGC]{3})\s+(\S)\s+([\d.]+)\s+([\d.]+)\s+\((\s*\d+)\)")

        # Process each line of the data
        for line in data.splitlines():
            if line.strip() == "":
                continue
            matches = pattern.findall(line)
            for match in matches:
                triplet, amino_acid, fraction, frequency, number = match
                # Convert necessary fields to appropriate types
                fraction = float(fraction)
                frequency = float(frequency)
                number = int(number.strip())
                result["triplet"][triplet] = [amino_acid, fraction, frequency, number]

        # Sort the dictionary first by amino acid and then by triplet
        sorted_triplets = sorted(result["triplet"].items(), key=lambda x: (x[1][0], x[0]))

        # Rebuild the result dictionary with sorted items
        sorted_result = {"triplet": OrderedDict(sorted_triplets)}

        # Convert dictionary to JSON format with separators for more compact representation
        json_output = json.dumps(sorted_result, indent=2, separators=(',', ': '))

        json_file_name = f"Kazusa_codon_frequency_table_{species_name}.json"
        json_path = os.path.join(GENERATED_FILES_DIR, json_file_name)

        # Save the JSON to a file
        with open(json_path, 'w') as f:
            f.write(json_output)

        # List files in the generated_files directory
        files = os.listdir(GENERATED_FILES_DIR)

        return render_template('index.html', files=files)

    # List files in the generated_files directory
    files = os.listdir(GENERATED_FILES_DIR)
    return render_template('index.html', files=files)

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(GENERATED_FILES_DIR, filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
