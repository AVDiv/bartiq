# Copyright 2024 PsiQuantum, Corp.
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

import ipywidgets as widgets
from ipytree import Node, Tree
from qref import SchemaV1
from qref.functools import accepts_all_qref_types
from qref.schema_v1 import RoutineV1
from traitlets import Tuple

from ..latex import routine_to_latex

DEFAULT_ROOT_NAME = ""


class _RoutineTree(Tree):
    """Tree object representing Routine."""

    routine_data = Tuple()

    def __init__(self, routine: RoutineV1 | SchemaV1, debug_mode: bool = False):
        super().__init__(multiple_selection=False)
        self._debug_mode = debug_mode
        self._node_routine_lookup: dict = {}
        self._build_tree(routine)
        self._add_click_events()
        self.root_node.selected = True

    def _build_tree(self, routine: SchemaV1 | RoutineV1) -> None:
        routine = routine if isinstance(routine, RoutineV1) else routine.program
        root_name = routine.name or DEFAULT_ROOT_NAME
        root_node = Node(root_name)
        self._node_routine_lookup[root_node] = routine
        self.root_node = root_node
        self.add_node(root_node)
        self._add_child_nodes(routine, root_node)

    def _add_child_nodes(self, routine: RoutineV1, node: Node) -> None:
        for child_routine in routine.children:
            child_node = Node(child_routine.name)
            self._node_routine_lookup[child_node] = child_routine
            node.add_node(child_node)
            self._add_child_nodes(child_routine, child_node)

    def _add_click_events(self, node: Node = None) -> None:
        node = node or self.root_node
        self._add_click_event(node)
        for child_node in node.nodes:
            self._add_click_events(child_node)

    def _add_click_event(self, node: Node) -> None:
        node.observe(self.handle_click, "selected")

    def handle_click(self, event: dict) -> None:
        if event["new"]:
            node = event["owner"]
            routine = self._node_routine_lookup[node]
            html_strings = routine_to_latex(routine, show_non_root_resources=self._debug_mode, paged=True)

            self.routine_data = tuple(widgets.HTMLMath(rf"{html_string}") for html_string in html_strings)


@accepts_all_qref_types
def explore_routine(routine: RoutineV1, tree_min_width="initial", resource_max_width="initial") -> widgets.HBox:
    """Widget faciliting exploration of routine's costs.

    Args:
        routine: [`Routine`][bartiq.Routine] object to analyze.
        tree_min_width: string defining the minimal width of the left part of the widget (tree).
            For pixel values, should be specified as "100px". Defaults to "initial".
        resource_max_width: string defining the minimal width of the right part of the widget (resources).
            For pixel values, should be specified as "100px". Defaults to "initial".
    """
    tree = _RoutineTree(routine)

    routine_display = widgets.VBox()
    widgets.dlink((tree, "routine_data"), (routine_display, "children"))

    left_box = widgets.VBox([tree], layout=widgets.Layout(min_width=tree_min_width))
    right_box = widgets.VBox([routine_display], layout=widgets.Layout(max_width=resource_max_width))
    return widgets.HBox([left_box, right_box])
