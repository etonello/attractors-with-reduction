#!/usr/bin/env sh
p="`realpath "$1"`"; shift
d="`dirname "$p"`"
b="`basename "$p"`"
docker run --rm -v "${d}":/d colomoto/attractors-with-reduction /d/"${b}" "${@}"
