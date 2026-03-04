import streamlit as st
import re
import uuid
import xml.etree.ElementTree as ET
from xml.dom import minidom
from datetime import datetime

# =========================================================
# CONFIG
# =========================================================

st.set_page_config(
    page_title="AADL Behavioral Annex → PNML",
    layout="wide"
)

st.title("AADL Behavioral Annex → PNML Translator")
st.markdown("Translate AADL Behavioral Annex into a Place/Transition Petri Net (PNML).")

# =========================================================
# UTILITY FUNCTIONS
# =========================================================

def generate_id(prefix):
    return f"{prefix}_{uuid.uuid4().hex[:8]}"

def prettify(elem):
    return minidom.parseString(
        ET.tostring(elem, 'utf-8')
    ).toprettyxml(indent="  ")

# =========================================================
# PARSER
# =========================================================

def parse_behavior_annex(aadl_text):
    states = []
    initial_state = None
    transitions = []

    # Extract states
    state_pattern = r"(\w+):\s*(initial\s+state|state);"
    for match in re.finditer(state_pattern, aadl_text):
        name, stype = match.groups()
        states.append(name)
        if "initial" in stype:
            initial_state = name

    # Extract transitions
    trans_pattern = r"(\w+)\s*-\[\s*(.*?)\s*\]->\s*(\w+)(?:\s*\{(.*?)\})?;"
    for match in re.finditer(trans_pattern, aadl_text):
        src, guard, dst, action = match.groups()
        transitions.append({
            "source": src.strip(),
            "target": dst.strip(),
            "guard": guard.strip() if guard else "",
            "action": action.strip() if action else ""
        })

    return states, initial_state, transitions

# =========================================================
# PNML GENERATOR
# =========================================================

def generate_pnml(states, initial_state, transitions):

    pnml = ET.Element("pnml")
    net = ET.SubElement(pnml, "net", {
        "id": generate_id("net"),
        "type": "http://www.pnml.org/version-2009/grammar/ptnet"
    })

    page = ET.SubElement(net, "page", {"id": generate_id("page")})

    place_map = {}

    # Create places
    for state in states:
        pid = generate_id("place")
        place_map[state] = pid

        place = ET.SubElement(page, "place", {"id": pid})
        name = ET.SubElement(place, "name")
        text = ET.SubElement(name, "text")
        text.text = state

        if state == initial_state:
            marking = ET.SubElement(place, "initialMarking")
            ET.SubElement(marking, "text").text = "1"

    # Create transitions
    for t in transitions:
        tid = generate_id("trans")

        transition = ET.SubElement(page, "transition", {"id": tid})

        name = ET.SubElement(transition, "name")
        ET.SubElement(name, "text").text = f"{t['source']}_to_{t['target']}"

        # Guard annotation
        if t["guard"]:
            ts = ET.SubElement(transition, "toolspecific", {
                "tool": "AADL-BA",
                "version": "1.0"
            })
            ET.SubElement(ts, "guard").text = t["guard"]

        # Action annotation
        if t["action"]:
            ts = ET.SubElement(transition, "toolspecific", {
                "tool": "AADL-BA",
                "version": "1.0"
            })
            ET.SubElement(ts, "action").text = t["action"]

        # Input arc
        ET.SubElement(page, "arc", {
            "id": generate_id("arc"),
            "source": place_map[t["source"]],
            "target": tid
        })

        # Output arc
        ET.SubElement(page, "arc", {
            "id": generate_id("arc"),
            "source": tid,
            "target": place_map[t["target"]]
        })

    return prettify(pnml)

# =========================================================
# UI
# =========================================================

default_example = """
states
   Idle: initial state;
   Active: state;
   Error: state;

transitions
   Idle -[ start ]-> Active { log_start; };
   Active -[ fail ]-> Error;
   Error -[ reset ]-> Idle;
"""

aadl_input = st.text_area(
    "Paste AADL Behavioral Annex here:",
    value=default_example,
    height=300
)

col1, col2 = st.columns(2)

with col1:
    parse_button = st.button("Parse Model")

with col2:
    generate_button = st.button("Generate PNML")

# =========================================================
# EXECUTION
# =========================================================

if parse_button:
    states, initial_state, transitions = parse_behavior_annex(aadl_input)

    st.subheader("Parsed Structure")
    st.write("States:", states)
    st.write("Initial State:", initial_state)
    st.write("Transitions:", transitions)

if generate_button:
    states, initial_state, transitions = parse_behavior_annex(aadl_input)

    if not states:
        st.error("No states detected.")
    elif not initial_state:
        st.error("No initial state defined.")
    else:
        pnml_output = generate_pnml(states, initial_state, transitions)

        st.success("PNML Generated Successfully")

        st.download_button(
            label="Download PNML File",
            data=pnml_output,
            file_name=f"aadl_petri_net_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pnml",
            mime="application/xml"
        )

        st.subheader("Generated PNML Preview")
        st.code(pnml_output, language="xml")