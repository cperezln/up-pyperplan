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
from typing import List, Dict, Tuple
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
from pyperplan.pddl.pddl import Predicate

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
        domAST = self.parse_domain(problem)
        # initialize the translation visitor
        visitor = TraversePDDLDomain()
        # and traverse the AST
        domAST.accept(visitor)
        # finally return the pddl.Domain
        dom = visitor.domain
        probAST = self.parse_problem(dom, problem)
        search = SEARCHES["bfs"]

        # initialize the translation visitor
        visitor = TraversePDDLProblem(dom)
        # and traverse the AST
        probAST.accept(visitor)
        # finally return the pddl.Problem
        task = _ground(visitor.get_problem())
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

    def parse_problem(self, domain: DomainDef, problem: Problem) -> ProblemDef:
        objects = [self._parse_object(o) for o in problem.all_objects()]
        init = self._parse_initial_values(problem)
        goal_formula = self._converter.convert_effect(problem.env.expression_manager.And(problem.goals()))
        goal = GoalStmt(goal_formula)
        return ProblemDef(problem.name(), domain.name, objects, init, goal)


    def _parse_initial_values(self, problem: Problem) -> InitStmt:
        pi_l: List[PredicateInstance] = []
        for f, v in problem.initial_values().items():
            if v != problem.env.expression_manager.TRUE():
                assert not v.bool_constant_value()
                continue
            obj_l: List[str] = []
            for o in f.args():
                obj_l.append(o.object().name())
            pi_l.append(PredicateInstance(f.fluent().name(), obj_l))
        return InitStmt(pi_l)



    def _parse_object(self, obj: UpfObject) -> PyperplanObject:
        return PyperplanObject(obj.name(), obj.type().name())

    def parse_domain(self, problem: Problem) -> DomainDef:
        keywords: List[Keyword] = [Keyword('strips')]
        if problem.kind().has_flat_typing(): # type: ignore
            keywords.append(Keyword('typing'))
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
            count = 0
            #predicate_signature
            pred_sign: List[Tuple[str, List[PyperplanType]]] = []
            for t in f.signature():
                pred_sign.append(tuple(f'a_{count}', [self._parse_type(t.name(), self._object_pyp_type)]))
                count = count + 1
            predicates.append(Predicate(n, pred_sign))
        actions: Dict[str, PyperplanAction] = {a.name(): self._parse_action(a, problem.env) for a in problem.actions().values()}
        return DomainDef(f'domain_{problem.name()}', RequirementsStmt(keywords), pyperplan_types, PredicatesStmt(predicates),  actions, None)

    def _parse_action(self, action: Action, env) -> PyperplanAction:
        #action_signature
        act_sign: List[Tuple[str, Tuple[PyperplanType, ...]]] = [tuple(p.name(),
            tuple(self._parse_type(p.type(), self._object_pyp_type))) for p in action.parameters()]
        precond: List[Predicate] = []
        for p in action.preconditions():
            if p.is_fluent():
                precond.append(Predicate(p.fluent().name(), ))
            elif p.is_parameter_exp():
                #NOTE Fondamentalmente trattano i parametri delle azioni come fossero dei fluenti!!!

        return PyperplanAction(action.name(), act_sign, , EffectStmt(effect))

    def _parse_effects(self, action: Action, env) -> FNode:
        effects = []
        for e in action.effects():
            if e.is_conditional():
                assert False #NOTE RAISEEEE
            if not e.value().is_bool_constant():
                assert False #NOTE raise
            if e.value().bool_constant_value():
                effects.append(e.fluent())
            else:
                effects.append(env.expression_manager.Not(e.fluent()))
        return env.expression_manager.And(effects)

    def _parse_action_parameter(self, parameter: ActionParameter) -> Variable:
        t = self._parse_type(parameter.type())
        return Variable(parameter.name(), [parameter.type().name()])

    def _parse_type(self, type: UpfType, parent: PyperplanType) -> PyperplanType:
        assert type.is_user_type()
        return PyperplanType(type.name(), parent)

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
