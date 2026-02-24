import re
import xml.etree.ElementTree as ET
from xml.dom import minidom


# ==========================================================
# AADL PARSER
# ==========================================================

class AADLParser:
    def __init__(self, file_path):
        self.file_path = file_path
        self.states = []
        self.initial_state = None
        self.transitions = []

    def parse(self):
        with open(self.file_path, "r") as f:
            content = f.read()

        # Extract states block
        states_block = re.search(r"states(.*?)transitions", content, re.DOTALL)
        if states_block:
            states_text = states_block.group(1)

            for line in states_text.split(";"):
                line = line.strip()
                if not line:
                    continue

                if "initial state" in line:
                    state_name = line.split(":")[0].strip()
                    self.states.append(state_name)
                    self.initial_state = state_name
                elif "state" in line:
                    state_name = line.split(":")[0].strip()
                    self.states.append(state_name)

        # Extract transitions block
        trans_block = re.search(r"transitions(.*?)};", content, re.DOTALL)
        if trans_block:
            trans_text = trans_block.group(1)

            pattern = r"(\w+)\s*-\[(.*?)\]->\s*(\w+)"
            matches = re.findall(pattern, trans_text)

            for src, guard, tgt in matches:
                self.transitions.append({
                    "source": src.strip(),
                    "guard": guard.strip(),
                    "target": tgt.strip()
                })

        return {
            "states": self.states,
            "initial_state": self.initial_state,
            "transitions": self.transitions
        }


# ==========================================================
# PNML GENERATOR
# ==========================================================

class PNMLGenerator:
    def __init__(self, aadl_model):
        self.model = aadl_model

    def generate(self, output_file):

        pnml = ET.Element("pnml")
        net = ET.SubElement(pnml, "net", {
            "id": "aadl_net",
            "type": "http://www.pnml.org/version-2009/grammar/ptnet"
        })

        page = ET.SubElement(net, "page", {"id": "page1"})

        # Create places
        for state in self.model["states"]:
            place = ET.SubElement(page, "place", {"id": state})

            name = ET.SubElement(place, "name")
            text = ET.SubElement(name, "text")
            text.text = state

            if state == self.model["initial_state"]:
                marking = ET.SubElement(place, "initialMarking")
                text = ET.SubElement(marking, "text")
                text.text = "1"

        # Create transitions
        for i, t in enumerate(self.model["transitions"]):
            tid = f"T{i}"
            transition = ET.SubElement(page, "transition", {"id": tid})

            name = ET.SubElement(transition, "name")
            text = ET.SubElement(name, "text")
            text.text = t["guard"] if t["guard"] else "true"

        # Create arcs
        for i, t in enumerate(self.model["transitions"]):
            tid = f"T{i}"

            # input arc
            ET.SubElement(page, "arc", {
                "id": f"a_in_{i}",
                "source": t["source"],
                "target": tid
            })

            # output arc
            ET.SubElement(page, "arc", {
                "id": f"a_out_{i}",
                "source": tid,
                "target": t["target"]
            })

        # Pretty print
        xml_str = ET.tostring(pnml, encoding="utf-8")
        parsed = minidom.parseString(xml_str)
        pretty_xml = parsed.toprettyxml(indent="  ")

        with open(output_file, "w") as f:
            f.write(pretty_xml)

        print(f"PNML file generated: {output_file}")


# ==========================================================
# MAIN
# ==========================================================

if __name__ == "__main__":

    aadl_file = "model.aadl"
    pnml_output = "model.pnml"

    parser = AADLParser(aadl_file)
    aadl_model = parser.parse()

    generator = PNMLGenerator(aadl_model)
    generator.generate(pnml_output)
