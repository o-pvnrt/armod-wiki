# Hardware Design

## Introduction

Given the rail distribution presented in the subsystem description, ICs are selected to fit the requirements given by the loads and battery. For the buck converters, the selected IC is the Texas Instruments TPS56637 (TPS56637RPAR), a 4.5 V to 28 V input, 6 A synchronous step-down converter with enable and power-good signaling, while the LDO required for the MCU is the onsemi NCP164C (NCP164CSN330T1G), a 300 mA fixed 3.3 V ultra-low-noise linear regulator with a power-good output. The battery manager and charger IC selected is the Analog Devices LTC4162-L (LTC4162EUFD-LAD), a 35 V, 3.2 A multi-cell Li-Ion synchronous step-down charger featuring integrated power path control and I2C telemetry.

In order to protect the converters and downstream chips, input protection is managed by the Texas Instruments LM74800-Q1 (LM74800QDRRRQ1), an ideal diode controller driving external back-to-back N-channel MOSFETs to provide reverse-polarity, reverse-current, and overvoltage protection (complemented by an 8 A input fuse and TVS diode).

This section therefore presents the schematic and circuit design of the power system, with a basic description of the PCB layout.

## Circuit Design
