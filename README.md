# DeepGEN - Antigenicity Prediction Tool (CLI)

DeepGEN is a command-line tool for predicting **protein antigenicity** from either FASTA sequences or PDB structures.
It integrates **three models** — ProtBERT embeddings, structural features, and physicochemical features — along with a **consensus-based predictor** to improve accuracy.

1. **ProtBERT** – transformer-based protein language model
2. **Structural features model** – trained on 3D structure-derived descriptors
3. **Physicochemical features model** – trained on sequence-based properties
4. **Consensus predictor** – combines predictions from all models (default)

---

## 📦 Features

- Input: **FASTA** or **PDB** files
- Output: `Antigenic` or `Non-antigenic`
- Choose a single model (`protbert`, `structural`, `physchem`) or a **consensus prediction**
- Easy to use via command line

---

## 🧠 Model Weights

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

## ⚠️ Prerequisite: DSSP

DSSP must be installed separately for structural feature extraction.

Ubuntu:
```bash
sudo apt-get install dssp
```

---

## ⚙️ Installation

Clone the repository and install required dependencies:

```bash
git clone https://github.com/KshitijaPawar01/DeepGen-antigenicity-prediction-tool.git
cd DeepGen-antigenicity-prediction-tool
pip install -r requirements.txt
```

Then download the ProtBERT checkpoint as shown above.

---

## 🚀 Usage

```bash
python predictor.py --input sequence.fasta --model consensus
```

**Options:**

| Flag | Description | Example |
|------|-------------|---------|
| `--input` | Path to input FASTA or PDB file | `--input protein.fasta` |
| `--model` | Model to use: `protbert`, `structural`, `physchem`, or `consensus` (default) | `--model protbert` |

**Example with a PDB structure:**

```bash
python predictor.py --input structure.pdb --model structural
```

**Output:**
