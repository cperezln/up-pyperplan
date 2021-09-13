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


import pyperplan.search as search
import os
import subprocess
import re
from typing import List, Dict, Set, Tuple
import upf
from upf.problem_kind import ProblemKind
from upf.problem import Problem
from upf.io.pddl_writer import PDDLWriter
from upf.exceptions import UPFException
from upf.action import Action, ActionParameter
from upf.fnode import FNode
from upf.types import Type as UpfType
from upf.object import Object as UpfObject
from upf.plan import ActionInstance, SequentialPlan

from pyperplan.pddl.pddl import Action as PyperplanAction
from pyperplan.pddl.pddl import Type as PyperplanType
from pyperplan.pddl.pddl import Problem as PyperplanProblem
from pyperplan.pddl.pddl import Predicate, Effect, Domain

from pyperplan.pddl.parser import DomainDef, ProblemDef, InitStmt, GoalStmt, ActionStmt, Variable
from pyperplan.pddl.parser import Formula, Keyword, RequirementsStmt, PredicatesStmt, PredicateInstance
from pyperplan.pddl.parser import PreconditionStmt, EffectStmt

from pyperplan.pddl.parser import Object as PyperplanObject
from pyperplan.pddl.tree_visitor import TraversePDDLProblem, TraversePDDLDomain

from pyperplan.planner import _ground, _search, SEARCHES, HEURISTICS

from upf_pyperplan.converter import ExpressionConverter


class SolverImpl(upf.Solver):
    def __init__(self, weight=None, heuristic=None, **options):
        self._converter = ExpressionConverter()

    # def solve(self, problem):
    #     pddl_writer = PDDLWriter(problem)
    #     pddl_writer.write_domain("pyperplan_domain.pddl")
    #     pddl_writer.write_problem("pyperplan_problem.pddl")
    #     cmd = "python3 pyperplan.py pyperplan_domain.pddl pyperplan_problem.pddl"
    #     res = subprocess.run(cmd, capture_output=True)

    #     if not os.path.isfile("pyperplan_problem.pddl.soln"):
    #         print(res.stderr.decode())
    #     else:
    #         plan = self._plan_from_file(problem, "pyperplan_problem.pddl.soln")

    #     return plan

    def solve(self, problem: Problem):
        self.pyp_types: Dict[str, PyperplanType] = {}
        dom = self.parse_domain(problem)
        prob = self.parse_problem(dom, problem)
        search = SEARCHES["bfs"]
        task = _ground(prob)
        print("TASK SBAGLIATO")
        print(task)
        heuristic = None
        # if not heuristic_class is None:
        #     heuristic = heuristic_class(task)
        solution = _search(task, search, heuristic)
        actions: List[ActionInstance] = []
        for action_string in solution:
            actions.append(self._parse_string_to_action_instance(action_string.name, problem))

        return SequentialPlan(actions)

    def _parse_string_to_action_instance(self, string: str, problem: Problem) -> ActionInstance:
        assert string[0] == "(" and string[-1] == ")"
        list_str = string[1:-1].split(" ")
        action = problem.action(list_str[0])
        param = tuple(problem.object(o_name) for o_name in list_str[1:])
        return ActionInstance(action, param)

    def parse_problem(self, domain: Domain, problem: Problem) -> PyperplanProblem:
        objects: Dict[str, PyperplanType] = {o.name(): self._parse_type(o.type(), self._object_pyp_type) for o in problem.all_objects()}
        init: List[Predicate] = self._parse_initial_values(problem)
        goal: List[Predicate] = self._parse_goal(problem)
        return PyperplanProblem(problem.name(), domain, objects, init, goal)

    def _parse_goal(self, problem: Problem) -> List[Predicate]:
        p_l: List[Predicate] = []
        for f in problem.goals():
            assert f.is_fluent_exp()
            obj_l: List[Tuple[str, Tuple[PyperplanType]]] = []
            for o in f.args():
                obj_l.append((o.object().name(), (self._parse_type(o.object().type(), self._object_pyp_type), )))
            p_l.append(Predicate(f.fluent().name(), obj_l))
            return p_l


    def _parse_initial_values(self, problem: Problem) -> List[Predicate]:
        p_l: List[Predicate] = []
        for f, v in problem.initial_values().items():
            if v != problem.env.expression_manager.TRUE():
                assert not v.bool_constant_value()
                continue
            obj_l: List[Tuple[str, PyperplanType]] = []
            for o in f.args():
                obj_l.append((o.object().name(), self._parse_type(o.object().type(), self._object_pyp_type)))
            p_l.append(Predicate(f.fluent().name(), obj_l))
            return p_l

    def _parse_object(self, obj: UpfObject) -> PyperplanObject:
        return PyperplanObject(obj.name(), obj.type().name())

    def parse_domain(self, problem: Problem) -> Domain:
        if problem.kind().has_negative_conditions(): # type: ignore
            raise
        if problem.kind().has_disjunctive_conditions(): # type: ignore
            raise
        if problem.kind().has_equality(): # type: ignore
            raise
        if (problem.kind().has_continuous_numbers() or # type: ignore
            problem.kind().has_discrete_numbers()): # type: ignore
            raise
        if problem.kind().has_conditional_effects(): # type: ignore
            raise
        if problem.has_type("object"):
            self._object_pyp_type = self._parse_type(problem.user_type("object"), None)
        else:
            self._object_pyp_type = PyperplanType("object", None)
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

    def _parse_action(self, action: Action, env) -> PyperplanAction:
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
            else:
                #preconditions must be a list of fluents.
                raise
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
        self.pyp_types[type.name] = new_t
        return new_t

    def _parse_expression(self, expression: FNode) -> Formula:
        pass

    def _plan_from_file(self, problem: 'upf.Problem', plan_filename: str) -> 'upf.Plan':
        actions = []
        with open(plan_filename) as plan:
            for line in plan.readlines():
                if re.match(r'^\s*(;.*)?$', line):
                    continue
                res = re.match(r'^\s*\(\s*([\w?-]+)((\s+[\w?-]+)*)\s*\)\s*$', line)
                if res:
                    action = problem.action(res.group(1))
                    parameters = []
                    for p in res.group(2).split():
                        parameters.append(problem.env._expression_manager.ObjectExp(problem.object(p)))
                    actions.append(upf.ActionInstance(action, tuple(parameters)))
                else:
                    raise UPFException('Error parsing plan generated by ' + self.__class__.__name__)
        return upf.SequentialPlan(actions)



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
