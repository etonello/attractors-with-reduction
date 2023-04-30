from collections import defaultdict
from colomoto.minibn import BooleanNetwork
from time import time
import subprocess

from syntactic_reduction import syntactic_reduction, reconstruct_state
from run_mtsNFVS import run_mtsNFVS, run_mts_checker_from_path
from run_AEON import find_attractors_with_AEON_from_booleannet

def matches(state, t, inds):
    for i in inds:
        if state[i]!=t[i]: return False
    return True

def get_containing(state, ts):
    for t, inds in ts:
        if matches(state, t, inds):
            return t
    return None

def restrict_bnet(f, var_names, t, ig):
    """Restrict f to the subspace t.
    Remove variables that are fixed."""
    succ = {a: set(ig.successors(a)) for a in f}
    csts = {f.v(var_names[i]): f.ba.TRUE if val == '1' else f.ba.FALSE
            for i, val in enumerate(t)}
    g = f.copy()
    for a in csts:
        for b in succ[a.obj]:
            if f.v(b) not in csts:
                g[b] = g[b].subs(csts).simplify()
        del g[a.obj]
    return g

def prepare_candidates(attractor_states, min_ts, var_names, initial_var_names, red_seq):
    """Classify candidate attractor states as
    univocal (in a minimal trap space that contains only one candidate state),
    nonminimal (found outside of minimal trap spaces),
    nonunivocal (in a minimal trap space that contains multiple candidate states).
    """
    # group trap spaces using their projection on the
    # variables of the reduced network (initial_var_names)
    groups = defaultdict(list)
    inds = [var_names.index(v) for v in initial_var_names]
    sub_ts = []
    for t in min_ts:
        sub_t = ''.join(t[i] for i in inds)
        inds_sub_t = tuple(i for i in range(len(initial_var_names)) if sub_t[i]!='-')
        inds_t = [i for i in range(len(var_names)) if t[i]!='-']
        groups[sub_t].append((t, inds_t))
        sub_ts.append((sub_t, inds_sub_t))

    ts_states = defaultdict(list)
    nonminimal = []
    for x in attractor_states:
        # construct candidate state from attractor
        # state of the reduced network
        state = dict(zip(initial_var_names, x))
        state = reconstruct_state(state, red_seq)
        state = ''.join('1' if state[v] else '0' for v in var_names)
        x = ''.join('1' if xi else '0' for xi in x)

        # find if candidate state is contained
        # in any minimal trap space
        sub_t = get_containing(x, sub_ts)
        if sub_t is None:
            nonminimal.append(state)
        else:
            t = get_containing(state, groups[sub_t])
            if t is None: nonminimal.append(state)
            else: ts_states[t].append(state)

    # if a trap space contains only one candidate state,
    # the candidate state identifies a cyclic attractor
    cyclic = [v for t in ts_states for v in ts_states[t] if len(ts_states[t])==1]
    # if a trap space contains more than one candidate state,
    # it might contain more than one attractor
    nonunivocal = {t: v for t, v in ts_states.items() if len(v)>1}
    return cyclic, nonminimal, nonunivocal

def get_candidates(f, var_names, method="AEON", verbose=False):
    """Compute the attractors of f and
    return one state from each cyclic attractor."""
    methods = ["AEON", "mtsNFVS"]
    if method not in methods:
        raise ValueError(f"Method must be one of {methods}.")
    if method=="AEON":
        attractors, model_var_names = find_attractors_with_AEON_from_booleannet(f, verbose=verbose)
        attractor_states = [a.pick_vertex().vertices().list_vertices()[0] for a in attractors if a.cardinality()>1]
        order = [model_var_names.index(v) for v in var_names]
        return [[a[i] for i in order] for a in attractor_states]
    if method=="mtsNFVS":
        bnet = "targets, factors\n" + f.source()
        _, attractor_states, _ = run_mtsNFVS(bnet, verbose=verbose)
        attractor_states = [a for a in attractor_states
                            if tuple(f[v](**dict(zip(var_names, tuple(ai=='1' for ai in a)))) for v in var_names)!=a]
        return [[ai=='1' for ai in a] for a in attractor_states]

def get_ts_trappist(bnet_path, var_names):
    """Compute the minimal trap spaces using trappist."""
    command = ["trappist", bnet_path]
    try:
        result = subprocess.run(command, stdout=subprocess.PIPE)
        result = result.stdout.decode('utf-8').split('\n')
        var_order = result[0].strip().split()
        order = [var_order.index(v) for v in var_names]
        for row in result[1:-1]:
            t = row.strip().replace(' ', '')
            yield ''.join(t[i] for i in order)
    except subprocess.CalledProcessError as e:
        print(e.stderr)
        raise ValueError("Failed to run trappist.")

def find_attractors_with_reduction(bnet_path, stop_at=None, max_product=None, candidate_method="AEON", simplify=True, verbose=False):
    """Find one state in each attractor of the asynchronous dynamics
    of the bnet, by first removing variables,
    finding attractors of the reduced network,
    then screening the candidate states."""

    if verbose: print("Reading bnet... ", end="", flush=True)
    f = BooleanNetwork(bnet_path)
    var_names = [a for a in f]
    n = len(var_names)
    if verbose: print(f"{n} variables.", flush=True)

    # simplification
    if simplify:
        if verbose: print(f"Simplifying... ", end="", flush=True)
        t0_simpl = time()
        for a in f:
            f[a] = f[a].simplify().literalize()
        time_simpl = time() - t0_simpl
        if verbose: print(f"done in {time_simpl:.2f} seconds.", flush=True)

    # check if some variables appear only as regulators
    ig = f.influence_graph()
    pred = {a: set(ig.predecessors(a)) for a in f}
    succ = {a: set(ig.successors(a)) for a in f}
    if any(p not in f for a in pred for p in pred[a]):
        undefined = set(p for a in pred for p in pred[a] if p not in f)
        print(f"Undefined update functions ({undefined}).", flush=True)
        return

    # find trap spaces
    t0_min_ts = time()
    if verbose: print(f"Calculating minimal trap spaces... ", end="", flush=True)
    min_ts = list(get_ts_trappist(bnet_path, var_names))
    time_min_ts = time() - t0_min_ts
    if verbose: print(f"{len(min_ts)} minimal trap spaces found with trappist in {time_min_ts:.2f} seconds.", flush=True)
    steady = [x for x in min_ts if '-' not in x]

    # reduction
    t0 = time()

    if stop_at is None:
        stop_at = int(n / 10)
    if max_product is None:
        max_product = int((n / 10) ** 2 / 2)

    if verbose: print(f"Eliminating variables (stop_at={stop_at}, max_product={max_product})... ", end='', flush=True)
    red_f, red_seq = syntactic_reduction(f,
                                         ig=ig,
                                         stop_at=stop_at,
                                         max_product=max_product,
                                         simplify=True,
                                         verbose=False)
    time_reduction = time() - t0
    n_reduced, e_reduced = len(red_f), len(red_f.influence_graph().edges())
    if verbose:
        print(f"preprocessing and reduction to {n_reduced} variables, {e_reduced} edges in {time_reduction:.2f} seconds.", flush=True)
    red_var_names = sorted([a for a in red_f])

    t0_cand = time()
    if verbose: print(f"Getting candidates using {candidate_method}... ", end="", flush=True)
    attractor_states = get_candidates(red_f, method=candidate_method, var_names=red_var_names, verbose=verbose)
    time_cand = time() - t0_cand
    if verbose: print(f"found {len(attractor_states)} candidates in {time_cand:.2f} seconds.", flush=True)

    # take one state per attractor, reconstruct original state

    if verbose: print(f"Prefiltering candidates... ", end="", flush=True)
    t0_filter = time()
    min_ts_no_steady = [x for x in min_ts if '-' in x]
    cyclic, candidates, nonunivocal = prepare_candidates(attractor_states, min_ts_no_steady, var_names, red_var_names, red_seq)
    time_filter = time() - t0_filter
    if verbose:
        print(f"done in {time_filter:.2f} seconds ({len(steady)} steady states, {len(cyclic)} cyclic so far).", flush=True)
        print(f"{len(candidates)} candidates, {len(nonunivocal)} nonunivocal min. trap spaces.", flush=True)

    # run nonminimal candidates through mtsNFVS model checker
    time_checker = 0
    if len(candidates)>0:
        if verbose: print(f"Running model checker... ", end="", flush=True)
        t0_checker = time()
        _, add_cyclic, _ = run_mts_checker_from_path(bnet_path, [a for a in f], min_ts, candidates)
        cyclic = cyclic + add_cyclic
        time_checker = time() - t0_checker
        if verbose: print(f"done in {time_checker:.2f} seconds (found {len(add_cyclic)}).", flush=True)

    # if there are nonunivocal candidate states, use AEON on the minimal trap space
    time_non_univ = 0
    if len(nonunivocal)>0:
        if verbose: print(f"Running AEON on {len(nonunivocal)} nonunivocal minimal trap spaces... ", end="", flush=True)
        t0_non_univ = time()
        for ts in nonunivocal:
            t = [ti for ti in ts if ti!='-']
            t_var_names = [var_names[i] for i in range(n) if ts[i]!='-']
            other_var_names = [var_names[i] for i in range(n) if ts[i]=='-']
            restricted_f = restrict_bnet(f, t_var_names, t, ig)
            states = get_candidates(restricted_f, other_var_names, method="AEON", verbose=verbose)
            states = [['1' if xi else '0' for xi in x] for x in states]
            t_dict = dict(zip(t_var_names, t))
            states = [dict(zip(other_var_names, x)) for x in states]
            for x in states: x.update(t_dict)
            states = [''.join(x[v] for v in var_names) for x in states]
            cyclic = cyclic + states
        time_non_univ = time() - t0_non_univ
        if verbose: print(f"done in {time_non_univ:.2f} seconds.", flush=True)

    if verbose: print(f"{len(steady)} steady, {len(cyclic)} cyclic.", flush=True)

    info = {}
    info["cand_mtd"] = candidate_method
    info["stop_at"] = stop_at
    info["max_prod"] = max_product
    info["n_nodes"] = n
    info["n_edges"] = len(ig.edges())
    info["n_red"] = n_reduced
    info["e_red"] = e_reduced
    info["n_cand"] = len(candidates)
    info["n_nuniv"] = len(nonunivocal)

    info["t_min_ts"] = time_min_ts
    info["t_simpl"] = time_simpl
    info["t_red"] = time_reduction
    info["t_cand"] = time_cand
    info["t_nuniv"] = time_non_univ
    info["t_checker"] = time_checker

    info["n_steady"] = len(steady)
    info["n_cyclic"] = len(cyclic)

    return steady, cyclic, info

if __name__=="__main__":
    import os
    bnet_dir = "networks/bio-models"
    candidates, nonunivocal = 0, 0
    for k, bnet_file in enumerate(sorted(os.listdir(bnet_dir))):
        bnet_path = os.path.join(bnet_dir, bnet_file)
        print(bnet_file, flush=True)
        t0 = time()
        result = find_attractors_with_reduction(bnet_path, stop_at=None, max_product=None, verbose=True, candidate_method="AEON")
        if result is not None:
            steady, cyclic, info = result
            print(f"{len(steady)} steady, {len(cyclic)} cyclic, {time() - t0:.1f} seconds.\n", flush=True)
            candidates += info["n_cand"]
            nonunivocal += info["n_nuniv"]
    print(f"{k+1} networks, {candidates} candidate nonmaximal states, {nonunivocal} candidate nonunivocal states.")
