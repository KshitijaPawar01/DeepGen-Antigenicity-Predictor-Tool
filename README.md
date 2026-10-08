# DeepGEN - Antigenicity Prediction Tool (CLI)

DeepGEN is a command-line tool for predicting **protein antigenicity** from either FASTA sequences or PDB structures.
It integrates **three models** — ProtBERT embeddings, structural features, and physicochemical features — along with a **consensus-based predictor** to improve accuracy.

1. **ProtBERT** – transformer-based protein language model, trained on sequence data
2. **Structural features model** – Gradient Boosting model trained on 43 structural descriptors extracted from 3D coordinates
3. **Physicochemical features model** – Gradient Boosting model trained on sequence-derived physicochemical properties
4. **Consensus predictor** – combines predictions from all applicable models, weighted by each model's validation accuracy (default)

---

## Features

- Input: **FASTA** (sequence only) or **PDB** (structure) files
- Output: `Antigenic` or `Non-antigenic`, with per-model probabilities and a consensus confidence score
- **FASTA input** → runs ProtBERT + physicochemical models, consensus of the two
- **PDB input** → runs ProtBERT + physicochemical **and** structural models, full 3-model consensus
- Easy to use via command line

---

## Model Weights

The ProtBERT checkpoint is hosted separately on Hugging Face Hub (too large for GitHub):

🔗 **https://huggingface.co/KshitijaPawar01/DeepGEN**

Download it with:

```python
from huggingface_hub import snapshot_download
snapshot_download(repo_id="KshitijaPawar01/DeepGEN", local_dir="./Models/checkpoint-334")
```

Or via CLI:

```bash
pip install huggingface_hub
hf download KshitijaPawar01/DeepGEN --local-dir ./Models/checkpoint-334
```

The Gradient Boosting models (`Physico_Gradient_Boosting.joblib`, `Structural_Gradient_Boosting.joblib`) are included directly in this repo under `Models/`.

---

## Prerequisite: DSSP

DSSP is required for structural feature extraction from PDB files (secondary structure assignment).

Ubuntu:
```bash
sudo apt-get install dssp
```

macOS (Homebrew):
```bash
brew install dssp
```

The tool calls the `mkdssp` binary — confirm it's on your `PATH` after installation (`which mkdssp`).

---

## Installation

Clone the repository and install required dependencies:

```bash
git clone https://github.com/KshitijaPawar01/DeepGen-Antigenicity-Predictor-Tool.git
cd DeepGen-Antigenicity-Predictor-Tool
pip install -r requirements.txt
```

Then download the ProtBERT checkpoint as shown above under **Model Weights**.

---

## Usage

```bash
python predictor.py <input_file> <file_type>
```

**Arguments:**

| Argument | Description | Example |
|----------|-------------|---------|
| `input_file` | Path to the input file | `sequence.fasta` or `structure.pdb` |
| `file_type` | Type of input — `fasta` or `pdb` | `fasta` |

**Example with a FASTA sequence** (2-model consensus: ProtBERT + physicochemical):

```bash
python predictor.py sequence.fasta fasta
```

**Example with a PDB structure** (full 3-model consensus, including structural features):

```bash
python predictor.py structure.pdb pdb
```

**Output:**

The tool prints a JSON summary to stdout and writes full results to `results/`:

```json
{
  "status": "success",
  "json_result": "results/result_1758950000.json",
  "csv_result": "results/result_1758950000.csv",
  "count": 1
}
```

Each result entry includes the final prediction, confidence, and each model's individual probability:

```json
{
  "Sequence_ID": "example_protein",
  "Final_Prediction": "Antigenic",
  "Confidence": 0.87,
  "ProtBERT_Score": 0.91,
  "Physicochemical_Score": 0.83,
  "Structural_Score": 0.78,
  "Consensus_Probability": 0.85
}
```

*(`Structural_Score` is `null` for FASTA input, since no 3D structure is available.)*

---

## Repository Structure

```
DeepGen-Antigenicity-Predictor-Tool/
├── Models/
│   ├── Physico_Gradient_Boosting.joblib
│   ├── Structural_Gradient_Boosting.joblib
│   ├── aaindex1.txt
│   └── checkpoint-334/        # Download from Hugging Face — not included here
├── examples/                  # Sample input files for testing
├── predictor.py
├── requirements.txt
└── README.md
```

---

## Performance

DeepGEN achieves **94.11% accuracy** on an independent dataset comprising experimentally validated vaccine candidate proteins. Individual model accuracies used for consensus weighting: ProtBERT 86%, physicochemical 86%, structural 73%.



## Contact

Kshitija Pawar — Bioinformatics Centre, Savitribai Phule Pune University.

Email - pkshitija2001@gmail.com
