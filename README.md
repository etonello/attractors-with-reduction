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

## Instructions

### Requirements
- [clingo](https://potassco.org/clingo)
- [colomoto-jupyter](https://github.com/colomoto/colomoto-jupyter)
- [trappist](https://github.com/soli/trap-spaces-as-siphons)
- [biodivine-aeon](https://github.com/sybila/biodivine-boolean-models)
- [mtsNFVS](https://github.com/giang-trinh/mtsNFVS)
- [Z3](https://github.com/Z3Prover/z3/releases/) -- libz3.so and libz3java.so must be in the LD_LIBRARY_PATH

### Installation
```
git submodule update --recursive --remote --init
pip install -r requirements.txt
```

### Usage

```
python attractor_computation.py file.bnet
```

See `--help` for configuraiton reduction and tool for computing attractors on
reduced network.

:warning: The warnings about missing MiniZinc are harmless.

## Docker image

- Pull image
    ```
    docker pull colomoto/attractors-with-reduction
    ```
- Get options
    ```
    docker run --rm colomoto/attractors-with-reduction --help
    ```
- Run on given Boolean network
    ```
    ./docker-run file.bnet [options..]
    ```
