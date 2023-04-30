import boolean
from networkx import in_degree_centrality, out_degree_centrality, selfloop_edges
import boolean.boolean as bpy

def candidate_list(ig):
    """Sort nodes by product of degree centralities."""
    icentrs = in_degree_centrality(ig)
    ocentrs = out_degree_centrality(ig)
    loops = [l[0] for l in selfloop_edges(ig)]
    centrs = {x: icentrs[x] * ocentrs[x] for x in ig.nodes() if x not in loops}
    return sorted(centrs, key=lambda k: centrs[k])

def get_node_min_product(pred, succ, max_product=100):
    """Return non-autoregulated node with minimum product of
    number of regulators and number of targets.
    """
    n_edges = {a: len(pred[a]) * len(succ[a]) for a in pred if a not in pred[a]}
    if len(n_edges)==0: return None
    if min(n_edges.values()) > max_product: return None
    return min(n_edges, key=n_edges.get)

def get_dependencies(bf):
    """Return variables of a Boolean function."""
    def var_of_lit(lit):
        if isinstance(lit, boolean.NOT):
            return lit.args[0].obj
        else:
            return lit.obj
    return {var_of_lit(l) for l in bf.get_literals()}

def trim_constants(f, succ):
    """Propagate and remove constants.
    Return list of pairs (variable, constant value).
    """
    def is_constant(fa):
        return isinstance(fa, (bpy._TRUE, bpy._FALSE))

    csts = {f.v(i): f.ba.TRUE if bool(fi) else f.ba.FALSE
                for i,fi in f.items() if is_constant(fi)}
    all_csts = csts.copy()
    while csts:
        new_csts = {}
        for a in csts:
            for b in succ[a.obj]:
                f[b] = f[b].subs(csts).simplify()
                if is_constant(f[b]):
                    sb = f.v(b)
                    if sb not in all_csts:
                        new_csts[sb] = f[b]
        all_csts.update(new_csts)
        csts = new_csts
    for a in all_csts:
        del f[a.obj]
    return [(i.obj, v) for i, v in all_csts.items()]

def syntactic_reduction(f, nodes=None, stop_at=1, max_product=100, simplify=False, ig=None, verbose=False):
    """Iterative elimination of non-autoregulated variables.
    Return reduced network and
    sequence of update functions of removed variables.
    """
    seq = []
    for a in f:
        f[a] = f[a].simplify().literalize()
    ig = ig or f.influence_graph()
    pred = {a: set(ig.predecessors(a)) for a in f}
    succ = {a: set(ig.successors(a)) for a in f}
    g = f.copy()
    n = len(g)
    if nodes is not None:
        use_nodes = True
        nodes = (a for a in nodes)
    else: 
        use_nodes = False
    while n > stop_at:
        a = next(nodes, None) if use_nodes else get_node_min_product(pred, succ, max_product=max_product)
        if a is None:
            if verbose: print("stopping")
            break
        if verbose: print(n, "nodes")
        if a in pred[a]:
            if verbose: print("skipping", a)
            continue
        sa = f.v(a)
        fa = g[sa]
        tr = {sa: fa}
        seq.insert(0, (a, fa))
        todel = []
        if verbose: print(f"removing {a} ({fa}) {succ[a]=}")
        for b in succ[a]:
            fb = g[b].subs(tr)
            if simplify:
                fb = fb.simplify().literalize()

                new_deps = get_dependencies(fb)
                todel += [(c, b) for c in pred[b] - new_deps]
                for c in new_deps:
                    succ[c].add(b)
                pred[b] = new_deps
            else:
                pred[b].remove(a)
                pred[b].update(pred[a])
                for c in pred[a]:
                    succ[c].add(b)

            g[b] = fb

        for (c, b) in todel:
            succ[c].remove(b)
        for c in pred[a]:
            succ[c].remove(a)

        del pred[a]
        del succ[a]
        del g[a]
        n -= 1
    csts = trim_constants(g, succ)
    seq = csts + seq
    return g, seq

def reconstruct_state(x, reduction_sequence):
    """From a Boolean state in the reduced space,
    and a sequence of update functions for the removed variables,
    reconstruct a state in the original network.
    """
    for a, fa in reduction_sequence:
        if fa == False: x[a] = 0
        elif fa == True: x[a] = 1
        else: x[a] = fa(**x)
    return x

if __name__ == "__main__":
    from argparse import ArgumentParser
    from colomoto.minibn import BooleanNetwork

    ap = ArgumentParser()
    ap.add_argument("bnet_file")
    ap.add_argument("nodes", nargs="*")
    ap.add_argument("--auto", choices=["centrality_at_start", "product"], default="centrality_at_start")
    ap.add_argument("--stop-at", type=int, default=20,
                        help="Stop when the reduced network has the given dimension")
    ap.add_argument("--simplify", action="store_true", default=False,
                        help="perform function simplification at each step")

    args = ap.parse_args()

    bnet_file = args.bnet_file
    f = BooleanNetwork(bnet_file)
    if args.simplify:
        for a, fa in f.items():
            f[a] = fa.simplify()

    ig = f.influence_graph()

    nodes = args.nodes
    if not nodes:
        if args.auto == "centrality_at_start":
            nodes = candidate_list(ig)
        if args.auto == "product":
            nodes = None

    red_f, red_seq = syntactic_reduction(f,
                                         nodes,
                                         ig=ig,
                                         stop_at=args.stop_at,
                                         simplify=args.simplify)
    print(red_f)
