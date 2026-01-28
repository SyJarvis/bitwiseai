---
name: asm-parser
description: "Parse 64-bit ASM instructions and files; analyze output errors with generated plots. Use cases: parse hardware instructions, verify instruction correctness, compare output files for numerical errors."
license: MIT
metadata:
  author: BitwiseAI
  version: "1.1.0"
---

# ASM Parser & Error Analyzer

## Features

This skill provides:
- Parse single 64-bit ASM instructions
- Parse all instructions from ASM files
- Support for multiple instruction formats (MOV, ADD, SUB, MUL, LUT2/3/4, SHIFT, CLAMP, ABS, etc.)
- Analyze errors between two numeric output files and generate plots

## Tools

### parse_asm_instruction

Parse a single 64-bit ASM instruction.

**Parameters**:
- `cmd` (string): 64-bit instruction value as integer, hex (0x...), or binary (0b...) format

**Example**:
```python
parse_asm_instruction("0x1234567890abcdef")
```

**Returns**:
JSON string containing:
- instruction name
- opcode (decimal, hex, binary)
- field details and register names

### parse_asm_file

Parse all instructions from an ASM file. File format: each line contains one or more instructions as hex (16 chars per instruction).

**Parameters**:
- `file_path` (string): path to ASM file

**Example**:
```python
parse_asm_file("/path/to/instructions.asm")
```

**Returns**:
JSON string with file path, instruction count, and detailed parsing of each instruction.

### analyze_errors

Compare two numeric output files and generate error analysis plots.

Reads numeric values from both files in order, computes absolute and relative errors, generates three PNG plots (absolute error, relative error, error distribution), saves detailed JSON results, and returns a concise summary.

**Parameters**:
- `file_a` (string): path to first file (e.g., model output)
- `file_b` (string): path to second file (e.g., reference/expected output)
- `outputs_dir` (string, optional): directory to save plots and JSON; defaults to 'outputs'

**Example**:
```python
analyze_errors("model_output.txt", "reference_output.txt", "outputs")
```

**Returns**:
Concise summary string containing:
- number of compared samples
- absolute error mean and max
- relative error mean and max
- path to detailed JSON results

**Output files**:
- `absolute_error.png` — line plot of absolute error vs sample index
- `relative_error.png` — line plot of relative error vs sample index
- `error_distribution.png` — histogram of absolute error distribution
- `error_analysis_{timestamp}.json` — detailed error statistics in JSON format

### analyze_errors_in_directory

Compare all files in a directory pairwise and generate error analysis for each pair.

Scans a directory for all text files (.txt, .dat), performs pairwise comparison between all files, saves results for each pair in separate subdirectories, and returns a batch summary.

**Parameters**:
- `directory_path` (string): path to directory containing files to compare
- `outputs_dir` (string, optional): base directory to write results into; defaults to 'outputs'

**Example**:
```python
analyze_errors_in_directory("./input_output_data", "outputs")
```

**Returns**:
Summary string containing:
- number of files found
- number of comparisons performed
- success/failure counts
- list of all comparison results with output directories

**Output structure**:
For each file pair (file_a vs file_b), creates a subdirectory:
- `{outputs_dir}/{file_a_name}_vs_{file_b_name}/` — contains plots and JSON for that pair

## Use Cases

- Parse and validate hardware instructions
- Analyze ASM files and convert formats
- Compare numerical outputs from model vs reference implementations
- Batch compare multiple output files in a directory
- Debug hardware verification errors
- Verify instruction correctness

## Supported Instruction Types

- MOV: Data movement
- ADD/SUB/MUL: Arithmetic operations
- LUT2/LUT3/LUT4: Lookup table operations
- SHIFT: Bit shifting
- CLAMP: Value clamping
- ABS: Absolute value

## Notes

- Instruction values must be 64-bit integers
- Error analysis requires numeric data in input files; non-numeric tokens are ignored
- Generated plots are saved as PNG files to the specified outputs directory
- Detailed error statistics are saved as JSON files (not printed to console)
- Directory comparison performs pairwise analysis of all text files found
- Requires numpy and matplotlib for error analysis functionality

