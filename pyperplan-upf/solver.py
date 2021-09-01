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


import os
import subprocess
import re
from typing import List
import upf
from upf.problem_kind import ProblemKind
from upf.problem import Problem
from upf.io.pddl_writer import PDDLWriter
from upf.exceptions import UPFException
from upf.action import Action, ActionParameter
from upf.fnode import FNode
from upf.types import Type as UpfType

from pddl.parser import DomainDef, ActionStmt, Variable, Formula, Keyword, RequirementsStmt, Predicate, PredicatesStmt
from pddl.parser import Type as PyperplanType

from upf_pyperplan.converter import ExpressionConverter

class SolverImpl(upf.Solver):
    def __init__(self, weight=None, heuristic=None, **options):
        pass

    def solve(self, problem: Problem):
        pddl_writer = PDDLWriter(problem)
        pddl_writer.write_domain("pyperplan_domain.pddl")
        pddl_writer.write_problem("pyperplan_problem.pddl")
        cmd = "python3 pyperplan.py pyperplan_domain.pddl pyperplan_problem.pddl"
        res = subprocess.run(cmd, capture_output=True)

        if not os.path.isfile("pyperplan_problem.pddl.soln"):
            print(res.stderr.decode())
        else:
            plan = self._plan_from_file(problem, "pyperplan_problem.pddl.soln")

        return plan

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
        if (self.problem.kind().has_continuous_numbers() or # type: ignore
            self.problem.kind().has_discrete_numbers()): # type: ignore
            raise
        if self.problem.kind().has_conditional_effects(): # type: ignore
            raise
        #NEED TYPES, a list of types
        predicates = []
        count = 0
        for n, f in problem.fluents().items():
            vars = []
            for t in f.signature():
                vars.append(Variable(f'a_{count}', [self._parse_type(t)]))
                count = count + 1
            predicates.append(Predicate(n, vars))


        return DomainDef(f'domain_{problem.name()}', types, RequirementsStmt(keywords), PredicatesStmt(predicates),  )





    def _parse_action(self, action: Action, env, converter) -> ActionStmt:
        var_list = [self._parse_action_parameter(p) for p in action.parameters()]
        precondition = converter.convert_precondition(env.expression_manager.And(action.preconditions()))
        effect = converter.conver_effect(self._parse_effects(action, env))
        return ActionStmt(action.name(), var_list, precondition, effect)

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
                effects.append(env.expression_manager.Not(e.fluent))
        return env.expression_manager.And(effects)

    def _parse_action_parameter(self, parameter: ActionParameter) -> Variable:
        t = self._parse_type(parameter.type())
        return Variable(parameter.name(), [t])

    def _parse_type(self, type: UpfType) -> PyperplanType:
        assert type.is_user_type()
        return PyperplanType(type.name())

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
                        parameters.append(problem._env._expression_manager.ObjectExp(problem.object(p)))
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
