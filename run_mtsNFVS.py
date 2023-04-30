import os
import shutil
import signal
import subprocess
import sys
import tempfile
from time import time

MTSNFVSPYTHONPATH = os.path.abspath('3rdparty/mtsNFVS/python/')
BIOLQMPATH = os.path.join(MTSNFVSPYTHONPATH, "bioLQM.jar")
MTSNFVSPATH = os.path.join(MTSNFVSPYTHONPATH, "mtsNFVS.jar")
EXTERNAL = os.path.join(MTSNFVSPYTHONPATH, "external")

def handle_sigterm(n, s):
    raise TimeoutError()

def save_trap_spaces(nodes, trap_spaces, filepath):
    with open(filepath, 'w') as mts_file:
         for node in nodes: print(f"{node},", file=mts_file)
         for k, t in enumerate(trap_spaces):
             print(f"min trap space {k + 1} : {t}", file=mts_file)

def save_candidates(nodes, candidates, filepath):
    with open(filepath, 'w') as std_file:
         for node in nodes: print(f"{node},", file=std_file)
         for k, state in enumerate(candidates):
             print(f"steady state {k + 1} : {state}", file=std_file)

def parse_result(result):
    steady, cyclic = [], []
    running_time = None
    n_candidates = 0
    for row in result.split('\n'):
        if row.startswith("Attractor"):
            if "cyclic" in row:
                cyclic.append(row[row.rfind(' ')+1:])
            if "fixed point" in row:
                steady.append(row[row.rfind(' ')+1:])
        if row.startswith("Running time"):
                running_time = row[15:-5]
    return steady, cyclic, running_time

def run_mts_checker_from_path(bnet_path, var_names, trap_spaces, candidate_states):
    with open(bnet_path, 'r') as f:
        bnet = f.read()
    return run_mts_checker(bnet, var_names, trap_spaces, candidate_states)

def run_mts_checker(bnet, var_names, trap_spaces, candidate_states):
    """Run mtsNFVS reachability analysis on the candidate states."""
    signal.signal(signal.SIGTERM, handle_sigterm)

    starting_dir = os.getcwd()
    bnet_name = "bnet"
    with tempfile.TemporaryDirectory() as tmpdirname:
        networkdir = os.path.join(tmpdirname, "networks")
        os.makedirs(networkdir)
        tempdir = os.path.join(tmpdirname, "temp")
        os.makedirs(tempdir)
        with open(os.path.join(tmpdirname, "networks", f"{bnet_name}.bnet"), "w") as f:
            print(bnet, file=f)
        shutil.copytree(EXTERNAL, os.path.join(tmpdirname, "external"))

        predatadir = os.path.join(tmpdirname, "predata")
        os.makedirs(predatadir)

        mtsfilepath = os.path.join(predatadir, f"{bnet_name}.mts")
        save_trap_spaces(var_names, trap_spaces, mtsfilepath)
        stdfilepath = os.path.join(predatadir, f"{bnet_name}.std")
        save_candidates(var_names, candidate_states, stdfilepath)
        anfilepath = os.path.join(predatadir, f"{bnet_name}.an")

        command = ["java", "-jar", BIOLQMPATH, f"networks/{bnet_name}.bnet", anfilepath]
        subprocess.run(command, cwd=tmpdirname)
        command = ["java", "-jar", MTSNFVSPATH, f"{bnet_name}.bnet", os.path.join(tmpdirname, "networks")]
        result = subprocess.run(command, cwd=tmpdirname, stdout=subprocess.PIPE)
        steady, cyclic, running_time = parse_result(result.stdout.decode('utf-8'))

    return steady, cyclic, running_time

def run_mtsNFVS_from_path(bnet_path, verbose=False):
    with open(bnet_path, 'r') as f:
        bnet = f.read()
    return run_mtsNFVS(bnet, verbose=verbose)

def run_mtsNFVS(bnet, verbose=False):
    """Run mtsNFVS.
    Based on mtsNFVS/python/test.py.
    """
    signal.signal(signal.SIGTERM, handle_sigterm)

    sys.path.insert(0, os.path.join(
            os.path.dirname(os.path.realpath(__file__)), MTSNFVSPYTHONPATH))
    import mtsNFVS
    from importlib import reload
    reload(mtsNFVS)
    
    bnet_name = "bnet"
    if verbose: print("Preparing files...")
    with tempfile.TemporaryDirectory() as tmpdirname:
        shutil.copy(os.path.join(MTSNFVSPYTHONPATH, "bioLQM.jar"), tmpdirname)
        shutil.copy(os.path.join(MTSNFVSPYTHONPATH, "mtsNFVS.jar"), tmpdirname)
        shutil.copytree(EXTERNAL, os.path.join(tmpdirname, "external"))

        networkdir = os.path.join(tmpdirname, "networks")
        os.makedirs(networkdir)
        resultdir = os.path.join(tmpdirname, "results")
        os.makedirs(resultdir)
        tempdir = os.path.join(tmpdirname, "temp")
        os.makedirs(tempdir)
        predatadir = os.path.join(tmpdirname, "predata")
        os.makedirs(predatadir)
        bn_file = os.path.join(tmpdirname, "networks", f"{bnet_name}.bnet")
        with open(bn_file, "w") as f:
            print(bnet, file=f)

        start_time = time()
        with open(os.path.join(tmpdirname, "predata", f"{bnet_name}.mts"), "w") as mts_file:
            with open(os.path.join(tmpdirname, "predata", f"{bnet_name}.std"), "w") as std_file:
                write_file_time = mtsNFVS.compute_attractors(bn_file,
                                                             mts_file=mts_file,
                                                             std_file=std_file,
                                                             result_file=None)
        if verbose: print(f"Done calculating candidates.", flush=True)
        
        an_file = f"predata/{bnet_name}.an"
        subprocess.run(['java', '-jar', 'bioLQM.jar', f"networks/{bnet_name}.bnet", an_file], cwd=tmpdirname)
        result = subprocess.run(['java', '-jar', 'mtsNFVS.jar', f"{bnet_name}.bnet"], cwd=tmpdirname, stdout=subprocess.PIPE)
        steady, cyclic, _ = parse_result(result.stdout.decode('utf-8'))
    
    running_time = time() - start_time - write_file_time
    if verbose: print(f"done in {round(running_time, 4)} seconds ({len(steady)} steady, {len(cyclic)} cyclic).", flush=True)

    return steady, cyclic, float(running_time)

if __name__=="__main__":
    from argparse import ArgumentParser
    ap = ArgumentParser()
    ap.add_argument("bnet_file")
    args = ap.parse_args()
    run_mtsNFVS_from_path(args.bnet_file, verbose=True)
