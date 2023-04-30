# Computation of attractors of asynchronous dynamics of Boolean networks with network reduction

This repository contains some scripts for the identification of attractors of Boolean networks
using elimination of variables.

The accepted format for a Boolean network is `bnet`.
The folder `networks` contains some examples.

The reduction is implemented in `syntactic_reduction.py` using [`colomoto.minibn`](https://github.com/colomoto/colomoto-jupyter).
The main algorithm is contained in `attractor_computation.py`.
It relies on either [AEON](https://github.com/sybila/biodivine-boolean-models)
or [mtsNFVS](https://github.com/giang-trinh/mtsNFVS)
for the computation of attractors of reduced networks,
and on [trappist](https://github.com/soli/trap-spaces-as-siphons)
for the computation of minimal trap spaces.

See the main in `attractor_computation.py` for an example of how to use the scripts.

## Requirements
- [colomoto-jupyter](https://github.com/colomoto/colomoto-jupyter)
- [trappist](https://github.com/soli/trap-spaces-as-siphons)
- [biodivine-aeon](https://github.com/sybila/biodivine-boolean-models)
- [mtsNFVS](https://github.com/giang-trinh/mtsNFVS)

In most environments, they can installed with the following commands:
```
git submodule update --recursive --remote --init
pip install -r requirements.txt
```
