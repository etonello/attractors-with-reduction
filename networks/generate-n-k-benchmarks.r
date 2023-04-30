library(BoolNet)
set.seed(0)
k <- 2
n_nets <- 10
for (h in 1:5) {
    n <- h * 100
    for (i in 1:n_nets) {
	net <- generateRandomNKNetwork(n, k)
        file <- paste("random-n-k-benchmarks/random-n-", formatC(n, width=4, format="d", flag="0"), "-k-", k, "-", i-1, ".bnet", sep="")
	print(file)
        saveNetwork(net, file)
    }
}
