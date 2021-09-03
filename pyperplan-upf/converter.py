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
#


import upf.walkers as walkers
import upf.operators as op
from typing import List
from upf.walkers.dag import DagWalker
from upf.fnode import FNode
from pddl.parser import Predicate, Variable, Formula, TypeFormula, TypeVariable, TypeConstant

#(self, expression: FNode, args: List[Formula]) -> Formula:
#Formula("or", args, TypeFormula)
class ExpressionConverter(DagWalker):
    def __init__(self):
        DagWalker.__init__(self)


    def convert_effect(self, expression: FNode) -> Formula:
        """Converts the given expression."""
        self.is_precondition = False
        f = self.walk(expression)
        if f.key != "and":
            return Formula("and", [f], TypeFormula)
        else:
            return f

    def convert_precondition(self, expression: FNode) -> Formula:
        """Converts the given expression."""
        self.is_precondition = True
        f = self.walk(expression)
        if f.key != "and":
            return Formula("and", [f], TypeFormula)
        else:
            return f

    def walk_and(self, expression: FNode, args: List[Formula]) -> Formula:
        # if len(args) == 0:
        #     return Formula("true", [], TypeConstant)
        # else:
        #     return Formula("and", args, TypeFormula)
        return Formula("and", args, TypeFormula)

    def walk_or(self, expression: FNode, args: List[Formula]) -> Formula:
        if len(args) == 0:
            return Formula("false", [], TypeConstant)
        else:
            return Formula("or", args, TypeFormula)

    def walk_not(self, expression: FNode, args: List[Formula]) -> Formula:
        assert len(args) == 1
        if self.is_precondition:
            assert False #NOTE raise some Exception
        return Formula("not", args, TypeFormula)

    def walk_fluent_exp(self, expression: FNode, args: List[Formula]) -> Formula:
        return Formula(expression.fluent().name(), args, TypeFormula)

    def walk_param_exp(self, expression: FNode, args: List[Formula]) -> Formula:
        assert len(args) == 0
        var = Variable(expression.parameter().name())
        return Formula(var, [], TypeVariable)

    def walk_object_exp(self, expression: FNode, args: List[Formula]) -> Formula:
        assert len(args) == 0
        return Formula(expression.object().name(), [], TypeConstant)

    @walkers.handles(set(op.ALL_TYPES) - {op.AND, op.OR, op.NOT, op.FLUENT_EXP, op.PARAM_EXP, op.OBJECT_EXP})
    def walk_error(self, expression: FNode, args: List[Formula]) -> Formula:
        assert False #NOTE raise some Exception
