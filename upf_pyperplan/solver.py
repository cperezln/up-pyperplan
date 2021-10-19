# Copyright 2021 AIPlan4EU project
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import re
from typing import List, Dict, Optional, Set, Tuple
import upf
from upf.problem_kind import ProblemKind
from upf.exceptions import UPFUnsupportedProblemTypeError
from upf.types import Type as UpfType

from pyperplan.pddl.pddl import Action as PyperplanAction
from pyperplan.pddl.pddl import Type as PyperplanType
from pyperplan.pddl.pddl import Problem as PyperplanProblem
from pyperplan.pddl.pddl import Predicate, Effect, Domain


from pyperplan.planner import _ground, _search, SEARCHES, HEURISTICS


class SolverImpl(upf.Solver):
    def __init__(self, weight=None, heuristic=None, **options):
        #NOTE here parameters like heuristic and the search can be configured
        self.planner_name = "Pyperplan"

    def solve(self, problem: 'upf.problem.Problem') -> Optional['upf.plan.SequentialPlan']:
        '''This function returns the SequentialPlan for the problem given in input.
        The planner used to retrieve the plan is "pyperplan" therefore only flat_typing
        is supported.'''
        self.pyp_types: Dict[str, PyperplanType] = {}
        dom = self._parse_domain(problem)
        prob = self._parse_problem(dom, problem)
        search = SEARCHES["bfs"]
        task = _ground(prob)
        heuristic = None
        # if not heuristic_class is None:
        #     heuristic = heuristic_class(task)
        solution = _search(task, search, heuristic)
        actions: List[upf.plan.ActionInstance] = []
        if solution is None:
            return None
        for action_string in solution:
            actions.append(self._parse_string_to_action_instance(action_string.name, problem))

        return upf.plan.SequentialPlan(actions)

    def _parse_string_to_action_instance(self, string: str, problem: upf.problem.Problem) -> upf.plan.ActionInstance:
        assert string[0] == "(" and string[-1] == ")"
        list_str = string[1:-1].split(" ")
        action = problem.action(list_str[0])
        param = tuple(problem.object(o_name) for o_name in list_str[1:])
        return upf.plan.ActionInstance(action, param)

    def _parse_problem(self, domain: Domain, problem: upf.problem.Problem) -> PyperplanProblem:
        objects: Dict[str, PyperplanType] = {o.name(): self._parse_type(o.type(), self._object_pyp_type) for o in problem.all_objects()}
        init: List[Predicate] = self._parse_initial_values(problem)
        goal: List[Predicate] = self._parse_goal(problem)
        return PyperplanProblem(problem.name(), domain, objects, init, goal)

    def _parse_goal(self, problem: upf.problem.Problem) -> List[Predicate]:
        p_l: List[Predicate] = []
        for f in problem.goals():
            assert f.is_fluent_exp()
            obj_l: List[Tuple[str, Tuple[PyperplanType]]] = []
            for o in f.args():
                obj_l.append((o.object().name(), (self._parse_type(o.object().type(), self._object_pyp_type), )))
            p_l.append(Predicate(f.fluent().name(), obj_l))
            return p_l

    def _parse_initial_values(self, problem: upf.problem.Problem) -> List[Predicate]:
        p_l: List[Predicate] = []
        for f, v in problem.initial_values().items():
            if not v.is_bool_constant():
                raise UPFUnsupportedProblemTypeError(f"Initial value: {v} of fluent: {f} is not True or False.")
            if v.bool_constant_value():
                obj_l: List[Tuple[str, PyperplanType]] = []
                for o in f.args():
                    obj_l.append((o.object().name(), self._parse_type(o.object().type(), self._object_pyp_type)))
                p_l.append(Predicate(f.fluent().name(), obj_l))
        return p_l

    def _parse_domain(self, problem: upf.problem.Problem) -> Domain:
        if problem.kind().has_negative_conditions(): # type: ignore
            raise UPFUnsupportedProblemTypeError(f"Problem: {problem} contains negative preconditions or negative goals. The solver Pyperplan does not support that!")
        if problem.kind().has_disjunctive_conditions(): # type: ignore
            raise UPFUnsupportedProblemTypeError(f"Problem: {problem} contains disjunctive preconditions. The solver Pyperplan does not support that!")
        if problem.kind().has_equality(): # type: ignore
            raise UPFUnsupportedProblemTypeError(f"Problem {problem} contains an equality symbol. The solver Pyperplan does not support that!")
        if (problem.kind().has_continuous_numbers() or # type: ignore
            problem.kind().has_discrete_numbers()): # type: ignore
            raise UPFUnsupportedProblemTypeError(f"Problem {problem} contains numbers. The solver Pyperplan does not support that!")
        if problem.kind().has_conditional_effects(): # type: ignore
            raise UPFUnsupportedProblemTypeError(f"Problem {problem} contains conditional effects. The solver Pyperplan does not support that!")
        if problem.has_type("object"):
            self._object_pyp_type = self._parse_type(problem.user_type("object"), None)
        else:
            self._object_pyp_type = PyperplanType("object", None)
            self.pyp_types["object"] = self._object_pyp_type
        pyperplan_types = [self._object_pyp_type] + [self._parse_type(t, self._object_pyp_type) for t in problem.user_types().values() if t.name() != "object"]
        predicates: Dict[str, Predicate] = {}
        for n, f in problem.fluents().items():
            #predicate_signature
            pred_sign: List[Tuple[str, Tuple[PyperplanType]]] = []
            for _, t in enumerate(f.signature()):
                pred_sign.append((f'a_{_}', (self._parse_type(t, self._object_pyp_type), )))
            predicates[n] = Predicate(n, pred_sign)
        actions: Dict[str, PyperplanAction] = {a.name(): self._parse_action(a, problem.env) for a in problem.actions().values()}
        return Domain(f'domain_{problem.name()}', pyperplan_types, predicates,  actions)

    def _parse_action(self, action: upf.action.Action, env) -> PyperplanAction:
        #action_signature
        act_sign: List[Tuple[str, Tuple[PyperplanType, ...]]] = [(p.name(),
            (self._parse_type(p.type(), self._object_pyp_type), )) for p in action.parameters()]
        precond: List[Predicate] = []

        for p in action.preconditions():
            if p.is_fluent_exp():
                signature: List[Tuple[str, Tuple[PyperplanType, ...]]] = [(param_exp.parameter().name(),
                                        (self._parse_type(param_exp.parameter().type(), self._object_pyp_type), ))
                                        for param_exp in p.args()]
                precond.append(Predicate(p.fluent().name(), signature))
            elif p.is_and():
                for fl in p.args():
                    if not fl.is_fluent():
                        raise UPFUnsupportedProblemTypeError(f"In precondition: {p} of action: {action} every son of an AND must be a FLUENT")
                    signature: List[Tuple[str, Tuple[PyperplanType, ...]]] = [(param_exp.parameter().name(),
                                        (self._parse_type(param_exp.parameter().type(), self._object_pyp_type), ))
                                        for param_exp in fl.args()]
                    precond.append(Predicate(p.fluent().name(), signature))
            else:
                raise UPFUnsupportedProblemTypeError(f"In precondition: {p} of action: {action} is not an AND or a FLUENT")
        effect = Effect()
        add_set: Set[Predicate] = set()
        del_set: Set[Predicate] = set()
        for e in action.effects():
            params: List[Tuple[str, Tuple[PyperplanType, ...]]] = [(p.parameter().name(),
                                        (self._parse_type(p.parameter().type(), self._object_pyp_type), ))
                                        for p in e.fluent().args()]
            assert not e.is_conditional()
            if e.value().bool_constant_value():
                add_set.add(Predicate(e.fluent().fluent().name(), params))
            else:
                del_set.add(Predicate(e.fluent().fluent().name(), params))
        effect.addlist = add_set
        effect.dellist = del_set
        return PyperplanAction(action.name(), act_sign, precond, effect)

    def _parse_type(self, type: UpfType, parent: PyperplanType) -> PyperplanType:
        assert type.is_user_type()
        t = self.pyp_types.get(type.name(), None)
        if t is not None:
            return t
        new_t = PyperplanType(type.name(), parent)
        self.pyp_types[type.name()] = new_t
        return new_t

    @staticmethod
    def supports(problem_kind):
        supported_kind = ProblemKind()
        supported_kind.set_typing('FLAT_TYPING')
        return problem_kind.features().issubset(supported_kind.features())

    @staticmethod
    def is_oneshot_planner():
        return True

    def destroy(self):
        pass
