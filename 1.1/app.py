# MIT License

# Copyright (c) 2024 styslxb

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from flask import Flask, request, render_template
import re
import json
import os

app = Flask(__name__)

# 定义JSON文件目录
JSON_DIRECTORY = 'json_files'

# 从JSON文件中读取密码子频率表
def read_codon_frequency_table(file_name):
    file_path = os.path.join(JSON_DIRECTORY, file_name)
    try:
        with open(file_path, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"Error: {file_name} not found.")
        return {}
    except json.JSONDecodeError:
        print(f"Error: {file_name} is not a valid JSON.")
        return {}

# 动态加载所有密码子表
def load_codon_tables():
    codon_tables = {}
    for file_name in os.listdir(JSON_DIRECTORY):
        if file_name.endswith('.json'):
            table_name = file_name.replace('.json', '')
            codon_tables[table_name] = read_codon_frequency_table(file_name)
    return codon_tables

codon_tables = load_codon_tables()

def parse_codon_frequency_table(codon_frequency_table):
    codon_usage_table = {}
    for triplet, values in codon_frequency_table['triplet'].items():
        amino_acid, fraction, frequency, number = values
        fraction = float(fraction)
        if amino_acid not in codon_usage_table:
            codon_usage_table[amino_acid] = []
        codon_usage_table[amino_acid].append((triplet, fraction))
    return codon_usage_table

parsed_codon_tables = {name: parse_codon_frequency_table(table) for name, table in codon_tables.items()}

def get_max_frequency_codon_table(codon_usage_table):
    return {aa: max(codons, key=lambda x: x[1])[0] for aa, codons in codon_usage_table.items()}

max_frequency_codon_tables = {name: get_max_frequency_codon_table(table) for name, table in parsed_codon_tables.items()}

def reverse_translate(protein_sequence, codon_table, forced_codon_table):
    valid_amino_acids = set(codon_table.keys()).union(forced_codon_table.keys())
    protein_sequence = ''.join([aa for aa in protein_sequence.upper() if aa in valid_amino_acids])
    
    rna_sequence = ''
    for amino_acid in protein_sequence:
        if amino_acid in forced_codon_table:
            rna_sequence += forced_codon_table[amino_acid]
        elif amino_acid in codon_table:
            rna_sequence += codon_table[amino_acid]
        else:
            raise ValueError(f"Invalid amino acid: {amino_acid}")
    return rna_sequence

@app.route('/', methods=['GET', 'POST'])
def index():
    rna_sequence = ""
    if request.method == 'POST':
        protein_sequence = request.form['protein_sequence']
        selected_codon_table_name = request.form['codon_table']
        forced_codons_input = request.form['forced_codons']

        # 选择密码子表
        selected_codon_table = max_frequency_codon_tables.get(selected_codon_table_name, {})

        # 处理强制选择的密码子
        forced_codon_table = {}
        for line in forced_codons_input.strip().split('\n'):
            if line.strip():
                try:
                    amino_acid, codon = line.split()
                    forced_codon_table[amino_acid] = codon
                except ValueError:
                    print(f"Invalid format in forced codons: {line}")

        # 仅保留代表氨基酸的字母并过滤无效氨基酸
        protein_sequence = ''.join([aa for aa in re.sub(r'[^A-Z*]', '', protein_sequence.upper()) if aa in selected_codon_table or aa in forced_codon_table])

        # 生成RNA序列
        try:
            rna_sequence = reverse_translate(protein_sequence, selected_codon_table, forced_codon_table)
        except ValueError as e:
            print(e)
            rna_sequence = "Error: Invalid input"

    return render_template('index.html', rna_sequence=rna_sequence, codon_tables=max_frequency_codon_tables.keys())

if __name__ == '__main__':
    app.run(debug=True)
