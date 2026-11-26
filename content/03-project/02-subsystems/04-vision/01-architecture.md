# Subsystem Description

## Introduction

To keep eye contact with people nearby and turn its head towards them naturally, the ARMoD needs an onboard camera capable of locating people standing in front of it. Placing this sensor directly in the head and connecting it to the Raspberry Pi 5 Single-Board Computer (SBC) keeps person tracking self-contained inside the module, without relying on the perception stack of the host AMR/AGV.

Choosing a camera for this role involves balancing several practical constraints. First of all, the sensor needs a high enough frame rate and clean shutter behaviour to limit motion blur when the head turns or the mobile base moves, while offering enough resolution for lightweight person-detection models without overloading the SBC. Physically, it must be compact and light enough to fit inside the head alongside the display without adding excessive load to the neck servos. Finally, it needs to stay well within the budget and have reliable stock availability so the ARMoD can be prototyped without supply delays and easily replicated by other research groups. In the following subsections, the main camera candidates and the sensor selected for the ARMoD are discussed.

## Camera Selection

To choose the vision sensor, commercially available modules suitable for embedded robotics were reviewed across four main groups: stereo depth and AI cameras, global-shutter boards, commercial USB webcams, and compact rolling-shutter CSI modules. The shortlisted candidates compared for the ARMoD are listed in Table 1:

<div align="center" markdown="1">

| Camera | Shutter | Interface | Sensor & Max Video Mode | Price (€) |
|:---:|:---:|:---:|:---:|:---:|
| Intel RealSense D435i | Mixed | USB-C 3.1 | 2 MP RGB (1920 × 1080 @ 30 fps); Depth @ 90 fps | 435 |
| Luxonis OAK-D Lite | Mixed | USB-C | 13 MP RGB (@ 35 fps); Stereo mono @ 117 fps | 320 |
| Arducam OV9281 (B0224) | Global | CSI-2 | 1 MP Mono (1280 × 800 @ 120 fps) | 73 |
| Arducam B0332 (OV9281) | Global | USB 2.0 | 1 MP Mono (1280 × 800 @ 120 fps) | 57 |
| Raspberry Pi Global Shutter | Global | CSI-2 | 1.6 MP Mono (1456 × 1088 @ 60 fps) | 45 (+ lens) |
| Raspberry Pi HQ Camera | Rolling | CSI-2 | 12.3 MP Colour (1332 × 990 @ 120 fps) | 44 (+ lens) |
| Logitech C270 | Rolling | USB 2.0 | 0.9 MP Colour (1280 × 720 @ 30 fps) | 22 |
| **Raspberry Pi Camera Module 3** | **Rolling** | **CSI-2** | **11.9 MP Colour (1536 × 864 @ 120 fps)** | **30** |

*Table 1: Shortlisted camera candidates compared for the ARMoD vision subsystem.*

</div>

### Depth and Stereo AI Cameras

Stereo depth and smart vision units such as the `Intel RealSense D435i` and the `Luxonis OAK-D Lite` are common in mobile robotics because they output 3D depth maps and, in the case of the OAK-D Lite, run neural networks directly on an onboard processor rather than on the SBC. However, for gaze rendering and head pan-and-tilt orientation, the ARMoD only needs the 2D position of a person in the camera frame, making stereo depth unnecessary. Also, at the given price ranges, either camera would also consume over a third of the total robot budget. 

### Global Shutter Modules

Because the camera is mounted on a moving pan-and-tilt head carried by a mobile robot, shutter type is an important consideration. A rolling shutter exposes an image row by row, which can introduce skew or motion blur during fast turns, whereas a global shutter exposes all pixels simultaneously and avoids this distortion. Global-shutter sensors also tend to pair modest resolutions (1 MP to 1.6 MP) with high frame rates (60 fps to 120 fps), which matches lightweight person-tracking pipelines well since input images are downscaled before inference anyway.

Even so, the available global-shutter options presented clear practical drawbacks. The official `Raspberry Pi Global Shutter Camera` is easier to source, but uses a C/CS-mount body that requires a separate lens costing an extra €30 to €50. Compact board-level cameras built around the monochrome `OV9281` sensor—such as the `Arducam OV9281 (B0224)` over CSI-2  and the `Arducam B0332` over USB 2.0 reach 120 fps, albeit in monochrome. Despite this their main limitation is availability, as (at the time of ordering for the initial prototyping), distributor lead times ranged from three to seven weeks. Relying on parts with long backorders delays prototyping, goes against keeping the ARMoD easy to source and replicate, and costs roughly twice as much as a standard camera module.

### Commercial USB Webcams

Off-the-shelf USB webcams such as the `Logitech C270` are inexpensive, widely in stock with immediate delivery, and work plug-and-play under Linux. For permanent integration inside the robot, though, they are awkward to mount, with their plastic enclosures taking up space in the head, and their thick, USB cables being stiff and complicating routing across the neck joints. Their rolling-shutter sensors are also capped at 30 fps and add USB bus overhead compared to a direct camera interface. For these reasons, a USB webcam was ruled out as the final head camera, although a `Logitech C270` was still ordered as a benchtop backup during early software development, also providing a built-in microphone for initial testing if necessary.

### Compact CSI-2 Camera Modules

Camera boards with a native CSI-2 interface connect straight to the Raspberry Pi 5 through a thin, flat ribbon cable, which routes the neck without much mechanical stiffness. Within this category, the `Raspberry Pi HQ Camera` shares the same C/CS-mount and lens cost concerns as the official Global Shutter model.

Instead, the **`Raspberry Pi Camera Module 3`** offers the best fit for the ARMoD. Its primary advantage is availability and cost as it is stocked consistently by major electronics distributors with 1–2 day delivery at a low price, supporting both rapid prototyping and straightforward replication. Measuring roughly 25 × 24 mm with an integrated autofocus lens (10 cm to infinity), it also fits easily beside the 7-inch display inside the head with negligible mass. While its 11.9 MP still resolution is higher than a person detector needs, binned and cropped video modes deliver 2304 × 1296 at 56 fps or 1536 × 864 at 120 fps before downscaling on the SBC. Running at up to 120 fps with short exposure times helps keep rolling-shutter blur small during normal head movements while keeping tracking latency low. For these reasons, the `Raspberry Pi Camera Module 3` was chosen for prototyping and as the intended primary camera, and if field testing on a moving base shows that rolling-shutter distortion during rapid head turns degrades tracking accuracy, a compact global-shutter module such as the `Arducam OV9281` remains a straightforward future upgrade once availability allows for it.
