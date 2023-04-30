from collections import defaultdict
from colomoto.minibn import BooleanNetwork
from biodivine_aeon import BooleanNetwork as ABooleanNetwork
from biodivine_aeon import SymbolicAsyncGraph, find_attractors
from time import time

def find_attractors_with_AEON_from_bnet(bnet, name="", verbose=False):
    """Find attractors of a bnet with AEON.
    Return the attractors and the list of variables of the AEON model."""
    model = ABooleanNetwork.from_bnet(bnet)
    stg = SymbolicAsyncGraph(model)
    model_var_names = [model.get_variable_name(v) for v in model.variables()]
    return find_attractors(stg), model_var_names

def format_aeon_variable(variable, expression, regulators, non_observable=True):
    """Aeon format for a variable. Position is 0,0."""
    neg_reg = '-|' + ('?' if non_observable else '')
    pos_reg = '->' + ('?' if non_observable else '')
    aeon_variable = [f"#position:{variable}:0,0"]
    for r, signs in regulators.items():
        signs = list(set(signs))
        if len(signs)==1:
            sign = signs[0]
            aeon_variable.append(f"{r} {neg_reg if sign==-1 else pos_reg} {variable}")
        else:
            aeon_variable.append(f"{r} -?? {variable}")
    aeon_variable += [f"${variable}: {expression}"]
    return aeon_variable

def booleannetwork_to_aeon(f, name, description=None, simplify=True):
    """Convert a BooleanNetwork to aeon format."""
    if simplify:
        for a in f:
            f[a] = f[a].simplify().literalize()
    ig = f.influence_graph()
    edges = list(ig.edges(data=True))

    aeon_format = [f"#name:{name}",
                   f"#description:{description if description else name}"]
    for variable in f:
        regulators = defaultdict(list)
        for e in edges:
            if e[1]==variable:
                regulators[e[0]].append(e[2]['sign'])
        aeon_format += format_aeon_variable(variable, f[variable], regulators)

    return '\n'.join(aeon_format)

def find_attractors_with_AEON_from_booleannet(f, name="", verbose=False):
    """Find attractors of a BooleanNetwork with AEON.
    Return the attractors and the list of variables of the AEON model."""
    if verbose: print("Loading as AEON network... ", end='', flush=True)

    t0_aeon = time()
    aeon_net = booleannetwork_to_aeon(f, name=name)
    model = ABooleanNetwork.from_aeon(aeon_net)
    time_aeon = time() - t0_aeon

    model_var_names = [model.get_variable_name(v) for v in model.variables()]

    if verbose:
        print(f"loaded network with {model.num_vars()} variables in {time_aeon:.2f} seconds.", flush=True)
        print("Calculating symbolic asynchronous graph... ", end='', flush=True)

    t0_symb = time()
    stg = SymbolicAsyncGraph(model)
    time_symb = time() - t0_symb
    if verbose: print(f"done in {time_symb:.2f} seconds.", flush=True)

    if verbose: print("Calculating attractors... ", end='', flush=True)

    t0_attrs = time()
    attractors = find_attractors(stg)
    time_aeon_attrs = time() - t0_attrs

    if verbose:
        print(f"{len(attractors)} attractors found by AEON in {time_aeon_attrs:.2f} seconds.", flush=True)

    return attractors, model_var_names
