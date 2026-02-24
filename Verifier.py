import xml.etree.ElementTree as ET
import z3


# ==========================================================
# PNML IMPORT
# ==========================================================

def import_pnml(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()

    places = []
    transitions = []
    input_arcs = []
    output_arcs = []
    initial_marking = []

    for place in root.findall(".//place"):
        pid = place.attrib["id"]
        places.append(pid)

        marking = place.find(".//initialMarking")
        if marking is not None:
            text = marking.find(".//text")
            if text is not None and text.text.strip() != "0":
                initial_marking.append(pid)

    for transition in root.findall(".//transition"):
        transitions.append(transition.attrib["id"])

    for arc in root.findall(".//arc"):
        source = arc.attrib["source"]
        target = arc.attrib["target"]

        if source in places and target in transitions:
            input_arcs.append((source, target))
        elif source in transitions and target in places:
            output_arcs.append((source, target))

    return {
        "places": places,
        "transitions": transitions,
        "input_arcs": input_arcs,
        "output_arcs": output_arcs,
        "initial_marking": initial_marking
    }


# ==========================================================
# VERIFIER CLASS
# ==========================================================

class Verifier:
    """Petri Net PNML Containment Verifier (Path-based)"""

    def __init__(self):
        self.cutpoints1 = []
        self.cutpoints2 = []
        self.paths1 = []
        self.paths2 = []
        self.matches1 = []
        self.unmatched1 = []
        self.contained = False

    # ------------------------------------------------------
    # CUTPOINT DETECTION
    # ------------------------------------------------------

    def find_cut_points(self, pn):
        out_transitions = {p: set() for p in pn["places"]}
        trans_to_places = {t: set() for t in pn["transitions"]}

        for (p, t) in pn["input_arcs"]:
            out_transitions[p].add(t)

        for (t, p) in pn["output_arcs"]:
            trans_to_places[t].add(p)

        cut_points = set()

        # Initial marking are cutpoints
        for p in pn["initial_marking"]:
            cut_points.add(p)

        # Branching places
        for p, outs in out_transitions.items():
            if len(outs) > 1:
                cut_points.add(p)

        # Sink places
        for p in pn["places"]:
            if len(out_transitions[p]) == 0:
                cut_points.add(p)

        # Loop detection
        def has_back_edge(start_place):
            stack = []
            visited = set()

            for t in out_transitions[start_place]:
                for p2 in trans_to_places[t]:
                    stack.append((p2, t))

            while stack:
                p, last_t = stack.pop()
                if p == start_place:
                    return True

                for t2 in out_transitions.get(p, []):
                    if (p, t2) not in visited:
                        visited.add((p, t2))
                        for p2 in trans_to_places[t2]:
                            stack.append((p2, t2))
            return False

        for p in pn["places"]:
            if has_back_edge(p):
                cut_points.add(p)

        return sorted(list(cut_points))

    # ------------------------------------------------------
    # PATH EXTRACTION
    # ------------------------------------------------------

    def extract_paths(self, pn, cutpoints):
        out_transitions = {p: set() for p in pn["places"]}
        trans_to_places = {t: set() for t in pn["transitions"]}

        for (p, t) in pn["input_arcs"]:
            out_transitions[p].add(t)

        for (t, p) in pn["output_arcs"]:
            trans_to_places[t].add(p)

        cutpoint_set = set(cutpoints)
        paths = []

        def dfs(current_place, current_path, visited, start_cut):
            if len(current_path) > 0 and current_place in cutpoint_set:
                paths.append({
                    "from": start_cut,
                    "to": current_place,
                    "transitions": list(current_path)
                })
                return

            for t in out_transitions.get(current_place, []):
                for p2 in trans_to_places[t]:
                    if (p2, t) not in visited:
                        visited.add((p2, t))
                        dfs(p2, current_path + [t], visited, start_cut)
                        visited.remove((p2, t))

        for cut in cutpoints:
            dfs(cut, [], set(), cut)

        return paths

    # ------------------------------------------------------
    # TRACE EQUIVALENCE CHECK
    # ------------------------------------------------------

    def are_traces_equivalent(self, t1, t2):
        return t1 == t2

    # ------------------------------------------------------
    # CONTAINMENT CHECK
    # ------------------------------------------------------

    def check_pnml_containment(self, pnml1_path, pnml2_path):
        pn1 = import_pnml(pnml1_path)
        pn2 = import_pnml(pnml2_path)

        self.cutpoints1 = self.find_cut_points(pn1)
        self.cutpoints2 = self.find_cut_points(pn2)

        self.paths1 = self.extract_paths(pn1, self.cutpoints1)
        self.paths2 = self.extract_paths(pn2, self.cutpoints2)

        self.unmatched1 = []
        self.matches1 = []

        for p1 in self.paths1:
            found = False
            for p2 in self.paths2:
                if self.are_traces_equivalent(
                        p1["transitions"],
                        p2["transitions"]):
                    found = True
                    self.matches1.append((p1, p2))
                    break

            if not found:
                self.unmatched1.append(p1)

        self.contained = not self.unmatched1
        return self.contained

    # ------------------------------------------------------
    # GETTERS
    # ------------------------------------------------------

    def is_contained(self):
        return self.contained

    def get_unmatched_paths(self):
        return self.unmatched1

    def get_matched_paths(self):
        return self.matches1

    def get_analysis_results(self):
        return {
            "cutpoints1": self.cutpoints1,
            "cutpoints2": self.cutpoints2,
            "paths1": self.paths1,
            "paths2": self.paths2,
            "matches1": self.matches1,
            "unmatched1": self.unmatched1,
            "contained": self.contained
        }


# ==========================================================
# MAIN
# ==========================================================

if __name__ == "__main__":

    verifier = Verifier()

    result = verifier.check_pnml_containment(
        "model1.pnml",
        "model2.pnml"
    )

    print("\n============================")
    print("Containment Result:", result)
    print("============================")

    if not result:
        print("\nUnmatched Paths:")
        for p in verifier.get_unmatched_paths():
            print(p)

    else:
        print("\nAll paths of Model1 are contained in Model2.")
