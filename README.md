# Pyperplan integration for unified-planning
[Pyperplan](https://github.com/aibasel/pyperplan) is a classical planner based on different search heuristics.
Pyperplan supports action based classical planning problems with hierarchical typing.


## Pyperplan engine

The Pyperplan engine supports **action-based planning**, with the following features:

 - **classical**: basic action models with symbolic state variables and hierarchical typing.
 - **optimization**: support for optimizing plans for metrics: `plan-length`

Provided engines:

 - **pyperplan**:
   - **oneshot planning**: Will return the first plan found, regardless of its quality.
   - **grounding**: Will return a grounded problem.
 - **pyperplan-opt**:
   - **oneshot planning**: Will return a provably optimal plan.


## Default configuration
The Pyperplan integration for unified-planning uses an heuristic search algorithm to solve the planning problem.
More specifically, the default search is a Weighted A* Search, with **hadd** as **heuristic**.

The custom parameters are:
- **search**: a string between **wastar**, **astar**, **gbf**, **bfs**, **ehs**, **ids** and **sat**,
- **heuristic**: a string between **hadd**, **hmax**, **hsa**, **hff**, **blind**, **lmcut** and **landmark**.

## Installation

To automatically get a version that works with your version of the unified planning framework, you can list it as a solver in the pip installation of ```unified_planning```:

```
pip install unified-planning[pyperplan]
```

If you need several solvers, you can list them all within the brackets.

You can also install the Pyperplan integration separately (in case the current version of unified_planning does not include Pyperplan or you want to add it later to your unified planning installation). With

```
pip install up-pyperplan
```

you get the latest version. If you need an older version, you can install it with:

```
pip install up-pyperplan==<version number>
```

If you need the latest pre-release version, you can install it with:

```
pip install --pre up-pyperplan
```
or if you already have a version installed:
```
pip install --pre --upgrade up-pyperplan
```

## Acknowledgments
<img src="https://www.aiplan4eu-project.eu/wp-content/uploads/2021/07/euflag.png" width="60" height="40">

This library is being developed for the AIPlan4EU H2020 project (https://aiplan4eu-project.eu) that is funded by the European Commission under grant agreement number 101016442.
