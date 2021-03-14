+++
title = "Archetypal Analysis"
description = "A quick introduction to archetypal analysis."
draft = false
[taxonomies]
categories = ["archetypal analysis"]
authors = ["Aleix Alcacer"]
+++

Archetypal anlalysis is a branch of statistics whose purpose is to search for
extreme cases, called archetypes, in a data set.
Having these extreme patterns facilitates the interpretation of the results
thanks to the principle of the opposites.


## Archetype Analysis (AA)

In archetype analysis, each archetype is defined as a convex combination of
the observations.
At the same time, each observation is approximated by a convex combination of
the archetypes.

### Method

Let \\(X\\) be a \\(n \times m\\) matrix with \\(n\\) observations and 
\\(m\\) variables.
The goal is to find a matrix \\(Z\\) of \\(k\\) \\(m\\)-dimensional archetypes.
For that, AA computes two matrices \\(\alpha\\) and \\(\beta\\) which minimize the 
residual squares sum

\\[
\begin{aligned}
    RSS = &\sum\_{i=1}^n\sum\_{j=1}^m \left\lVert x\_{ij} - \hat{x}\_{ij} \right\rVert^2 \cr
        = &\sum\_{i=1}^n\sum\_{j=1}^m \left\lVert x\_{ij} - \sum\_{g=1}^k \alpha\_{ig} z\_{gj} \right\rVert^2 \cr
        = &\sum\_{i=1}^n\sum\_{j=1}^m \left\lVert x\_{ij} - \sum\_{g=1}^k \alpha\_{ig} \left( \sum\_{l=1}^n \beta\_{gl} x\_{lj}   \right) \right\rVert^2
\end{aligned}
\\]

under the constraints

1. \\(\sum\_{j=1}^k \alpha\_{ij} = 1\\) with \\(\alpha\_{ij} \geq 0\\)
for \\(i = 1, \ldots, n \\).
2. \\(\sum\_{l=1}^n \beta\_{jl} = 1\\) with \\(\beta\_{jl} \geq 0\\)
for \\(j = 1, \ldots, k \\).
