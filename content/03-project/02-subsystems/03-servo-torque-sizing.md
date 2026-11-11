# Servo torque sizing

This page explains how the joint torques used to size the arm servos were calculated.
The numbers come from the `Calculations` sheet of `spreadsheets/servo-design.ods` in the
`armod-tools` repository; the servo candidates are in the `Options` sheet of the same file.

## Approach

Each arm is treated as a two-link planar chain (upper arm and forearm) carrying a small
payload at the hand. For every joint the torque is estimated in its **worst-case static
pose**, that is, with the arm stretched out horizontally so that every mass has the longest
possible lever arm about the joint. Three contributions are then stacked:

1. **Static torque** – holding the links, the downstream servos and the payload against gravity.
2. **Dynamic torque** – accelerating the same masses from rest at a chosen angular acceleration.
3. **Friction margin** – a factor on the sum to cover friction and other unmodelled losses.

$$
\tau_{req} = SF_{fric}\,\left(\tau_{static} + \tau_{dyn}\right)
$$

## Joints and worst-case poses

| Joint | Motion | Worst-case pose used |
|-------|--------|----------------------|
| J1 | Shoulder pitch | Arm straight and horizontal, pointing forward |
| J2 | Shoulder roll | Arm straight and horizontal, out to the side (T-pose) |
| J3 | Upper-arm rotation (yaw) | Elbow bent 90°, forearm horizontal |
| J4 | Elbow flexion | Forearm horizontal |

J1 and J2 see the same load (the whole arm at full reach), and so do J3 and J4 (the forearm
and payload at full reach), so there are only two torque cases to calculate.

## Inputs

| Symbol | Meaning | Value | Unit |
|--------|---------|------:|------|
| $L_1$ | Upper-arm length (shoulder to elbow) | 0.12 | m |
| $L_2$ | Forearm length (elbow to hand) | 0.08 | m |
| $d_{J3}$ | Distance from the shoulder to the J3 servo | 0.05 | m |
| $m_{load}$ | Payload at the hand | 0.030 | kg |
| $m_{fa}$ | Forearm link mass | 0.0227 | kg |
| $m_{ua}$ | Upper-arm link mass | 0.0340 | kg |
| $m_{J3}$, $m_{J4}$ | Servo mass at J3 and at the elbow | 0.060 | kg |
| $g$ | Gravity | 9.81 | m/s² |
| $\alpha$ | Angular acceleration | 2 | rad/s² |

The link masses are not measured. Each link is modelled as a hollow printed PLA tube with
outer diameter $D_o = 5$ cm, inner diameter $D_i = 4.7$ cm (1.5 mm wall) and density
$\rho = 1.24$ g/cm³:

$$
m_{link} = \rho \, \frac{\pi}{4} \left(D_o^2 - D_i^2\right) L
$$

This gives about 23 g for the forearm and 34 g for the upper arm.

!!! note
    These are bare-tube masses. Brackets, infill and fasteners are not included, so the
    real links will be heavier; see [Open points](#open-points).

## Static torque

The payload and the servos are point masses; each link's weight acts at its mid-point.

**Elbow (J4) and upper-arm rotation (J3)**

$$
\tau_{J4} = m_{load}\, g\, L_2 + m_{fa}\, g\, \frac{L_2}{2}
$$

| Contribution | Lever arm | Torque (N·m) |
|--------------|-----------|-------------:|
| Payload | $L_2$ | 0.0235 |
| Forearm | $L_2/2$ | 0.0089 |
| **Total J3, J4** | | **0.0324** |

**Shoulder (J1 and J2)**

$$
\tau_{J2} = m_{load}\, g\, (L_1 + L_2) + m_{fa}\, g \left(L_1 + \frac{L_2}{2}\right)
          + m_{J4}\, g\, L_1 + m_{ua}\, g\, \frac{L_1}{2} + m_{J3}\, g\, d_{J3}
$$

| Contribution | Lever arm | Torque (N·m) |
|--------------|-----------|-------------:|
| Payload | $L_1 + L_2$ | 0.0589 |
| Forearm | $L_1 + L_2/2$ | 0.0356 |
| Elbow servo | $L_1$ | 0.0706 |
| Upper arm | $L_1/2$ | 0.0200 |
| J3 servo | $d_{J3}$ | 0.0294 |
| **Total J1, J2** | | **0.2145** |

The servos and the payload, not the printed links, make up most of the shoulder torque:
the elbow servo alone is a third of it.

## Dynamic torque

The torque needed to accelerate the arm is $\tau_{dyn} = I\,\alpha$, with $I$ the moment of
inertia of everything downstream of the joint, taken about the joint axis. Point masses
contribute $m r^2$ and a link rotating about its own end contributes $\tfrac{1}{3} m L^2$.

**Elbow (J4) and upper-arm rotation (J3)**

$$
I_{J4} = m_{load}\, L_2^2 + \tfrac{1}{3}\, m_{fa}\, L_2^2
$$

**Shoulder (J1 and J2)**

$$
I_{J2} = m_{load}\,(L_1 + L_2)^2 + m_{fa} \left(L_1 + \frac{L_2}{2}\right)^2
       + m_{J4}\, L_1^2 + \tfrac{1}{3}\, m_{ua}\, L_1^2 + m_{J3}\, d_{J3}^2
$$

The forearm is treated here as a point mass at its mid-point; its inertia about its own
centre is small by comparison and is neglected.

| Joints | $I$ (kg·m²) | $\tau_{dyn}$ at 2 rad/s² (N·m) |
|--------|------------:|-------------------------------:|
| J3, J4 | 0.00024 | 0.0005 |
| J1, J2 | 0.00296 | 0.0059 |

At this acceleration the dynamic term is under 3 % of the static one: the sizing is
dominated by holding the arm against gravity.

## Required torque

Servo data sheets quote stall torque in kg·cm, so the results are converted with
1 N·m = 10.2 kg·cm. The friction margin used is $SF_{fric} = 1.5$.

| Joints | Static (N·m) | Dynamic (N·m) | Sum (N·m) | Sum (kg·cm) | With margin 1.5 (kg·cm) |
|--------|-------------:|--------------:|----------:|------------:|------------------------:|
| J3, J4 | 0.0324 | 0.0005 | 0.0329 | 0.34 | **0.50** |
| J1, J2 | 0.2145 | 0.0059 | 0.2204 | 2.25 | **3.37** |

## Comparison with the servo candidates

The preferred architecture in the `Options` sheet uses ten servos of two sizes: the larger
one for shoulder pitch and roll, the smaller one for upper-arm rotation, elbow flexion and
the head.

| Joints | Required (kg·cm) | Servo | Stall torque (kg·cm) | Stall / required |
|--------|-----------------:|-------|---------------------:|-----------------:|
| J1, J2 | 3.37 | Dynamixel XL430-W250-T | 15.3 | 4.5 |
| J3, J4 | 0.50 | Dynamixel XL330-M288-T | 5.3 | 10.5 |

The head joints are not part of this calculation.

## Open points

- **Link masses.** The bare-tube estimate is a lower bound. The real printed parts
  (brackets, infill, fasteners) will weigh more, so the link masses should be replaced by
  CAD or weighed values. As a sensitivity check, links ten times heavier (227 g and 340 g)
  would raise the requirement to 11.2 kg·cm for J1/J2 and 1.7 kg·cm for J3/J4.
- **Safety factor on the static case.** The spreadsheet has a separate safety factor for
  the static torques, currently set to 1.
- **Payload.** 30 g at the hand is an assumption; the result for J1/J2 should be re-checked
  once the hand design is known.
- **Head and other joints** have not been sized yet, but will use one of the two servos selected.
