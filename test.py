import os
import pytest

from attractor_computation import find_attractors_with_reduction
from run_AEON import find_attractors_with_AEON_from_bnet
from run_mtsNFVS import run_mtsNFVS_from_path

bnet_folder = "networks/test-bnets"
bnet_files = sorted([os.path.join(bnet_folder, filename)
                     for filename in os.listdir(bnet_folder)
                     if filename.endswith(".bnet")])
attr_files = [filepath + ".attrs" for filepath in bnet_files]

def get_attractors(attr_file):
    steady, cyclic = [], []
    with open(attr_file, 'r') as atf:
        for row in atf:
            a = row.strip().split(' ')
            if len(a)==1:
                steady.append(a[0])
            else:
                cyclic.append(a)
    return sorted(steady), cyclic

def compare_attractors(steady, true_steady, cyclic, true_cyclic):
    assert sorted(steady) == true_steady
    assert len(cyclic) == len(true_cyclic)
    for a in true_cyclic:
        assert any(x in cyclic for x in a)

def compare_number_of_attractors(steady, true_steady, cyclic, true_cyclic):
    assert len(steady) == len(true_steady)
    assert len(cyclic) == len(true_cyclic)

@pytest.mark.parametrize("bnet_file, attr_file", zip(bnet_files, attr_files))
@pytest.mark.parametrize("candidate_method", ["AEON", "mtsNFVS"])
def test_attractors_reduction(bnet_file, attr_file, candidate_method):
    steady, cyclic, _ = find_attractors_with_reduction(bnet_file,
                                                       stop_at=1,
                                                       max_product=100,
                                                       candidate_method=candidate_method)
    true_steady, true_cyclic = get_attractors(attr_file)
    compare_number_of_attractors(steady, true_steady, cyclic, true_cyclic)

@pytest.mark.parametrize("bnet_file, attr_file", zip(bnet_files, attr_files))
def test_attractors_AEON(bnet_file, attr_file):
    with open(bnet_file, 'r') as bnf:
        bnet = bnf.read()
    var_names = [row.strip().split(',')[0] for row in bnet.split('\n')
                 if row!="targets, factors" and len(row)>0]
    attractors, model_var_names = find_attractors_with_AEON_from_bnet(bnet)
    attractors = [a.vertices().list_vertices() for a in attractors]
    order = [model_var_names.index(v) for v in var_names]
    attractors = [[''.join('1' if x[i] else '0' for i in order) for x in a] for a in attractors]
    steady = [a[0] for a in attractors if len(a)==1]
    cyclic = [a for a in attractors if len(a)>1]

    true_steady, true_cyclic = get_attractors(attr_file)

    assert sorted(steady) == true_steady
    assert sorted([sorted(list(a)) for a in cyclic]) == \
           sorted([sorted(list(a)) for a in true_cyclic])

@pytest.mark.parametrize("bnet_file, attr_file", zip(bnet_files, attr_files))
def test_attractors_mtsNFVS(bnet_file, attr_file):
    steady, cyclic, _ = run_mtsNFVS_from_path(bnet_file)
    true_steady, true_cyclic = get_attractors(attr_file)
    compare_attractors(steady, true_steady, cyclic, true_cyclic)
