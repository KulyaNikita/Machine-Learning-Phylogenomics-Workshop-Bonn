# Bonn: Machine Learning Phylogenomics


Welcome to this hands-on workshop in machine learning phylogenomics.<br>
In this tutorial we are going to use [PhyloAI](https://github.com/KulyaNikita/PhyloAI) a machine learning software for phylogenetic tree reconstructions.

## Dataset

We will use the following vertebrate data included in this repository:

- `data/vertebrate.fas` — protein alignment of 23 taxa with 9,587 aligned sites.
- `data/vertebrate_reference.tre` — a reference tree topology.

There are 8,855 possible four-taxon combinations. We will reconstruct a tree from the alignment with PhyloAI and compare its topology with the reference.

## First let's clone this repository

Clone the repository and enter the workshop directory:

```bash
git clone https://github.com/KulyaNikita/Machine_Learning_Phylogenomic_Workshop_Bonn.git
cd Machine_Learning_Phylogenomic_Workshop_Bonn
```

## Install PhyloAI

Install [Miniforge](https://github.com/conda-forge/miniforge) (recommended) or another conda distribution, then run:

```bash
conda create -n phyloai -c conda-forge -c bioconda phyloai
conda activate phyloai
phyloai download-models
phyloai check
```

- `conda create` creates the `phyloai` environment and installs PhyloAI and its dependencies from conda-forge and Bioconda.
- `conda activate phyloai` activates the environment.
- `phyloai download-models` downloads and verifies the pretrained networks.
- `phyloai check` checks the installed packages, supporting programs, and models.

For training networks on an Intel Mac, add `python=3.11` to the `conda create` command.

To inspect the available workflow options:

```bash
phyloai run --help
```

## Reconstruct the Vertebrate Tree

To reconstruct a tree run:

```bash
phyloai run --alignment data/vertebrate.fas --output results_vertebrate
```

This selects a substitution model, predicts quartet topologies, and combines them with [ASTRAQ](https://github.com/KulyaNikita/ASTRAQ). Use a new output directory for each run.
The inferred tree is saved as `results_vertebrate/astraq.tre`.

If `phyloai download-models` fails, use the included pre-downloaded Q.insect model instead:

```bash
phyloai run --alignment data/vertebrate.fas --models pre-downloaded_newtwork --substitution-model Q.insect --output results_vertebrate
```

What other output files are generated?

## Tree Visualization and Comparison

Create a figure of both the reference tree and your reconstructed tree. Install the plotting dependencies in the active environment, then run:

```bash
conda install -c conda-forge biopython matplotlib
python3 visualise_tree.py data/vertebrate_reference.tre --output figures/vertebrate_reference
python3 visualise_tree.py results_vertebrate/astraq.tre --output figures/vertebrate_inferred
```

Each command saves a PDF cladogram under `figures/`.

Open the two figures side by side and compare their topologies. What differences do you see? Which relationships agree, and which taxa or groups have different placements? 

## Simulate Training Data

Next, we will simulate protein quartet data and train our own **PhyloAI** network.

```bash
phyloai simulate \
  -substitution_model Qinsect \
  --training-scheme training_scheme.txt \
  -processes 4 --batch-size 100 \
  -output_dir simulations
```
Each row in [training_scheme.txt](training_scheme.txt) specifies an alignment length and a replicate count. 

This uses PolyMoSim to simulate Q.insect protein data at every length in the scheme;

The scheme includes lengths from 50 to 10,000 sites and generates **744 examples**. The frequency array needs approximately **0.48 GB** of disk space.

Three matching NumPy arrays are saved in `simulations/`:

- `site_pattern_frequencies_Qinsect_scheme_training_scheme.npy` — 160,000 amino-acid site-pattern frequencies per example.
- `trainTopoClass_Qinsect_scheme_training_scheme.npy` — quartet topology labels: 0 = AB|CD, 1 = AC|BD, 2 = AD|BC.
- `trainLength_Qinsect_scheme_training_scheme.npy` — raw alignment lengths for the length-aware network.

What are the amino-acid site-pattern frequencies? 

## Train a custom network

Train a PhyloAI network using the simulated frequencies, labels, and lengths:

```bash
phyloai train \
  --training-data simulations/site_pattern_frequencies_Qinsect_scheme_training_scheme.npy \
  --topology-data simulations/trainTopoClass_Qinsect_scheme_training_scheme.npy \
  --length-data simulations/trainLength_Qinsect_scheme_training_scheme.npy \
  --substitution-model Q.insect \
  --epochs 10 --threads 4 \
  --output-dir trained/Qinsect
```

The defaults select 10,000 informative patterns using Fisher scores and train a B1 network. 

The `trained/Qinsect/` directory contains the network, metadata, Fisher selector, training history, split indices, and selected feature array. Keep the network with its matching metadata and selector.

What training and validation accuracies did you obtain? If there is a gap between these accuracies, what does it mean? How might the small training dataset affect predictions on new alignments?

## Reconstruct a Tree with Your Custom Model

Use your newly trained PhyloAI network to reconstruct another tree from `data/vertebrate.fas`:

```bash
phyloai run \
  --alignment data/vertebrate.fas \
  --models trained/Qinsect \
  --substitution-model Q.insect \
  --output results_vertebrate_custom
```

`--models` points to the directory containing your trained network and its matching metadata and selector. `--substitution-model Q.insect` skips automatic model selection and uses your Q.insect network. The inferred tree is saved as `results_vertebrate_custom/astraq.tre`.

Visualize the new tree and compare it side by side with your previous reconstruction. Is the topology different? Why might the two models produce different trees? If the trees are identical, does that necessarily mean the models made the same quartet predictions?

You have completed the tutorial. You are amazing, congratulations!
