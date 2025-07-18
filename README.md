# 🔎 AADL-LLM-Verifier

**AADL-LLM-Verifier** is a research prototype that detects *hallucinations* introduced during the transformation of AADL (Architecture Analysis and Design Language) models, particularly when transformations are generated using Large Language Models (LLMs). It leverages Petri net semantics to ensure behavioral consistency and transformation validity.

---

## 🎯 Objective

- ✅ Verify correctness of LLM-generated transformations.
- 🚫 Detect unjustified insertions (hallucinations) in the model.
- 🧠 Use formal models (Petri nets) to compare semantics before and after transformation.

---

## 📘 Source AADL Model (S)

```aadl
system SafeCycleSystem
end SafeCycleSystem;

system implementation SafeCycleSystem.impl
    subcomponents
        sensor: thread Sensor.impl;
        processor: thread Processor.impl;
        actuator: thread Actuator.impl;
    connections
        conn1: port sensor.out_event -> processor.in_event;
        conn2: port processor.out_event -> actuator.in_event;
end SafeCycleSystem.impl;

thread Sensor
features
    out_event: out event port;
end Sensor;

thread implementation Sensor.impl
end Sensor.impl;

thread Processor
features
    in_event: in event port;
    out_event: out event port;
end Processor;

thread implementation Processor.impl
end Processor.impl;

thread Actuator
features
    in_event: in event port;
end Actuator;

thread implementation Actuator.impl
end Actuator.impl;
```

## Transformation Rules

| Rule ID | Name                         | Description                                                                 |
|--------:|------------------------------|-----------------------------------------------------------------------------|
| R1      | Add Monitoring Thread        | Adds a `Monitor` thread with a `fault_signal` port to monitor system faults. |
| R2      | Extend Sensor Interface      | Adds a `safe_mode` port to the `Sensor` component interface.                |
| R3      | Fault Detection Logic        | Connects `Monitor.fault_signal` to `Sensor.safe_mode` for fault propagation.|
| R4      | System Implementation Switch | Defines a new `system implementation` using additional components.          |

## Transformed AADL model (T)

```aadl
system SafeCycleSystem
end SafeCycleSystem;

system implementation SafeCycleSystem.transformed
    subcomponents
        sensor: thread Sensor.impl;
        processor: thread Processor.impl;
        actuator: thread Actuator.impl;
        monitor: thread Monitor.impl;
    connections
        conn1: port sensor.out_event -> processor.in_event;
        conn2: port processor.out_event -> actuator.in_event;
        conn3: port monitor.fault_signal -> sensor.safe_mode;
end SafeCycleSystem.transformed;

thread Sensor
features
    out_event: out event port;
    safe_mode: in event port;
end Sensor;

thread implementation Sensor.impl
end Sensor.impl;

thread Processor
features
    in_event: in event port;
    out_event: out event port;
end Processor;

thread implementation Processor.impl
end Processor.impl;

thread Actuator
features
    in_event: in event port;
end Actuator;

thread implementation Actuator.impl
end Actuator.impl;

thread Monitor
features
    fault_signal: out event port;
end Monitor;

thread implementation Monitor.impl
end Monitor.impl;
```
## Source Petri net Model
### Petri Net Model: Source AADL System

This Petri net models the basic **Sensor → Processor → Actuator** flow from the source AADL model. It ensures sequential execution and token-safe transitions.

### 📊 Petri Net Diagram (DOT)

You can render this graph using [Graphviz](https://graphviz.org/) or online tools like [WebGraphviz](https://dreampuf.github.io/GraphvizOnline/).

<details>
<summary>Click to expand DOT code</summary>

```dot
digraph SourcePetriNet {
    rankdir=LR;

    node [shape=circle];
    s_ready [label="Sensor Ready"];
    sp_data [label="Sensor->Processor"];
    p_ready [label="Processor Ready"];
    pa_data [label="Processor->Actuator"];
    a_ready [label="Actuator Ready"];

    node [shape=rectangle];
    s_exec [label="Sensor Exec"];
    p_exec [label="Processor Exec"];
    a_exec [label="Actuator Exec"];

    s_ready -> s_exec;
    s_exec -> sp_data;

    sp_data -> p_exec;
    p_ready -> p_exec;
    p_exec -> pa_data;

    pa_data -> a_exec;
    a_ready -> a_exec;
    a_exec -> s_ready;
}
```

## Tranforemd Petri net model 
### Petri Net Model: Transformed AADL System

This Petri net models the **transformed AADL system** with a fault-monitoring mechanism and a safe-mode reinitialization. It extends the original sensor–processor–actuator pipeline with runtime monitoring support.

### 📊 Petri Net Diagram (DOT)

You can render this extended model using [Graphviz](https://graphviz.org/) or online tools like [WebGraphviz](https://dreampuf.github.io/GraphvizOnline/).

<details>
<summary>Click to expand DOT code</summary>

```dot
digraph TransformedPetriNet {
    rankdir=LR;

    node [shape=circle];
    s_ready [label="Sensor Ready"];
    sp_data [label="Sensor->Processor"];
    p_ready [label="Processor Ready"];
    pa_data [label="Processor->Actuator"];
    a_ready [label="Actuator Ready"];
    m_ready [label="Monitor Ready"];
    fault_detected [label="Fault Detected"];

    node [shape=rectangle];
    s_exec [label="Sensor Exec"];
    p_exec [label="Processor Exec"];
    a_exec [label="Actuator Exec"];
    m_exec [label="Monitor Exec"];
    switch_mode [label="Switch to Safe Mode"];

    s_ready -> s_exec;
    s_exec -> sp_data;

    sp_data -> p_exec;
    p_ready -> p_exec;
    p_exec -> pa_data;

    pa_data -> a_exec;
    a_ready -> a_exec;
    a_exec -> s_ready;

    m_ready -> m_exec;
    m_exec -> fault_detected;
    fault_detected -> switch_mode;
    switch_mode -> s_ready;
}
```

