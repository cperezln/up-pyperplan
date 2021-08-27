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
import upf
from upf.problem_kind import ProblemKind
from upf.io.pddl_writer import PDDLWriter
from upf.io.pddl_reader import PDDLReader


class SolverImpl(upf.Solver):
    def __init__(self, weight=None, heuristic=None, **options):
        pass

    def solve(self, problem):
        pddl_writer = PDDLWriter(problem)
        pddl_writer.write_domain("pyperplan_domain.pddl")
        pddl_writer.write_problem("pyperplan_problem.pddl")
        run_command = "python3 pyperplan.py pyperplan_domain.pddl pyperplan_problem.pddl"
        os.system(run_command)



    @staticmethod
    def supports(problem_kind):
        supported_kind = ProblemKind()
        return problem_kind.features().issubset(supported_kind.features())

    @staticmethod
    def is_oneshot_planner():
        return True

    def destroy(self):
        pass
