# Subsystem Description

## Introduction

The ARMoD requires a computing platform capable of orchestrating the motions and actions of the robot, as well as communicating with the mounted AMV/AMR. This is derived from the necessity to keep the system agnostic to the vehicle to which is mounted, leading to the the implementation of a processor with enough capacity to run small vision models (for gazing mechanisms), display visuals on a screen (to convey the gaze as well as any other information) and interfacing through ROS2.

Different commercially available products meet these functional requirements, but few do so in a cost and power budget efficient manner. In the following subsections the computing platform selection is discussed, along with its functional and physical architecture.

## Platform Selection

To choose the main processor of the robot, several existing humanoid and expressive robotic platforms were reviewed first to compare what hardware they use. Even though these robots differ in size and purpose, the available computing options mostly fall into three groups: standard PCs and mini-PCs, NVIDIA Jetson boards, and single-board computers (SBCs) like the Raspberry Pi. A list of reference platforms and their processors is shown in Table 1.

<div align="center" markdown="1">

| Platform | Computing Unit |
|:---:|:---:|
| DARwIn-OP | Intel Atom 1.6 GHz |
| Asimov v1 | Raspberry Pi 5 |
| Berkeley Humanoid Lite | Intel N95 Mini PC |
| Fauna Sprout | NVIDIA Jetson AGX Orin |
| InMoov | Full Computer |
| pib | Raspberry Pi 5 (8 GB) |
| Poppy Project | Raspberry Pi 4 Model B |
| Reachy 2 | BEDROCK V3000 BASIC |
| Reachy Mini | Raspberry Pi Compute Module 4 |
| Robotis AI Sapiens | NVIDIA Jetson Orin NX (16 GB) |
| Roboto Origin | Orange Pi 5 Plus |
| SoftBank NAO | Intel Atom E3845 |
| ToddlerBot | NVIDIA Jetson Orin NX |
| YAREN | NVIDIA Jetson Nano |

*Table 1: Computing units used in similar humanoid and expressive robotic platforms.*

</div>

### PCs and Mini-PCs

Standard computers and x86 mini-PCs provide plenty of processing power and can run Linux and ROS2 out of the box without compatibility issues. However, using an external desktop or laptop (as done in stationary setups like InMoov) requires cables to an outside machine, which goes against keeping the ARMoD self-contained and independent of the mobile base. Using an onboard mini-PC or an industrial computer (such as in Berkeley Humanoid Lite or Reachy 2) solves this, but these units are still bulky, heavy, more expensive, and usually need active cooling. In addition, they generally require higher supply voltages (between 12 V and 19 V) and draw much more power under load, which complicates the battery and power design for an amount of computing power that the ARMoD does not actually need.

### NVIDIA Jetson Family

NVIDIA Jetson boards are very common in robotics whenever cameras and AI models are used, since they include a dedicated GPU. Still, none of the options in this line fit the project budget and requirements well. High-end modules like the Jetson Orin NX and AGX Orin (used in ToddlerBot, Robotis AI Sapiens, and Fauna Sprout) are meant for heavy deep learning and full-body control, so they are far too expensive and power-hungry for running small gaze models, especially considering the total budget of the robot. On the cheaper end, the older Jetson Nano (used in YAREN) has a reasonable price, but its hardware is outdated and NVIDIA no longer updates its official Ubuntu and JetPack versions, which makes running current ROS2 distributions difficult without extra workarounds like Docker containers. The newer Jetson Orin Nano fixes this software limitation, yet it is still much more expensive than a regular SBC, takes up more space with its carrier board, and consumes more power for a GPU that would barely be used.

### Raspberry Pi Family

ARM single-board computers, and especially the Raspberry Pi line (used in Poppy Project, Reachy Mini, Asimov v1, and pib), offer the best balance between price, power consumption, and ease of use for the ARMoD. Compared to other SBC brands like Orange Pi, Raspberry Pi boards are easier to source, have much better community and software support for Linux and ROS2, and include ready-to-use ports for the camera, the screen, and the UART link to the microcontroller. They also run directly from a 5 V line, which fits nicely with the rest of the electrical architecture and keeps power consumption low. Within this family, the Raspberry Pi 5 (8 GB) was chosen over the Raspberry Pi 4 Model B with the same 8 GB of RAM. For only an approximate €30 more, the Raspberry Pi 5 brings a noticeable jump in CPU speed, giving enough room to run the small vision models for gazing, update the screen, and handle wireless ROS2 communication at the same time.

## Functional Architecture

Once the Raspberry Pi 5 is selected as the main processor, its role in the robot can be broken down into the high-level tasks it runs. As shown in Figure 1, the software on the SBC is organised into six functional blocks. Solid arrows in the diagram represent internal data flow within the SBC, while dashed arrows represent digital links to other subsystems. At a general level, information coming from the main robot through ROS2 drives the spoken messages, gestures, gaze cues, and LED states, while local camera tracking updates where the eyes and head point.

![SBC functional architecture](_images/computing-functional-architecture-drawio.png){: .center }

*Figure 1: Functional architecture of the SBC (Raspberry Pi 5).*
{: .center }

### ROS Communication

This block manages the wireless link over Wi-Fi between the SBC and the ROS nodes running on the main mobile robot. Its main job is to gather context from the base through three tasks: receiving the robot's internal operational state, receiving its potential navigation paths, and receiving relevant sensor data. This information gives the SBC the context needed to trigger appropriate speech, gestures, facial cues, and LED patterns, while the two-way connection also allows the ARMoD to report its own state back to the main system, if implemented in the AMR/AMV.

### Speech

The Speech block produces the voice messages used to warn or inform people nearby, especially when they are not looking directly at the robot. Internally, it follows three steps: selecting a suitable predefined phrase for the current situation, running a Text-to-Speech (TTS) engine to generate the voice signal, and sending the digital audio output to the Digital-to-Analog Converter (DAC) of the audio subsystem, which then passes it on to the amplifier and speaker.

### Facial Expressions

The Facial Expressions block controls what is shown on the head display, which is currently dedicated to the robot's eyes. It calculates the target gaze direction, renders the eye graphics accordingly, and sends the resulting video frames over a digital link to the screen. Together with state cues from the main robot, this block receives direct internal data from the Person Tracking block so that the rendered eyes can follow a person standing in front of the ARMoD.

### Person Tracking

To maintain eye contact and orient the head naturally, the SBC needs to know where people are relative to the robot. The Person Tracking block communicates over a two-way digital link with the head camera to configure the sensor and acquire image frames. It then runs a small vision model for person detection and outputs the detected person's position. Within the SBC, this position data is sent directly to both the Facial Expressions block and the Movement Orchestration block.

### Movement Orchestration

Rather than controlling the motors directly, the SBC decides at a high level which movements the ARMoD has to perform. This block combines arm gesture selection, used to point in a direction or express internal states, with head pan and tilt orientation towards the person detected by the tracking pipeline. Both types of motion are turned into high-level movement requests and passed internally to the MCU Communication block instead of going straight to external hardware.

### MCU Communication

The MCU Communication block acts as the hardware interface between the Raspberry Pi 5 and the microcontroller over a two-way UART link. On the outgoing side, it transmits the movement requests coming from Movement Orchestration so the MCU can handle low-level servo control, and sends LED pattern requests to indicate operational or error states. On the incoming side, it receives servo and power state feedback from the MCU, keeping the SBC aware of joint status and battery levels.
