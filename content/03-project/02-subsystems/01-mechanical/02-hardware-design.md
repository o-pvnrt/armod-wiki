# Hardware Design

## Servo Selection

This page explains how the joint torques used to size the arm servos were calculated, and
compares them with the servo candidates.

### Approach

Each arm is treated as a two-link chain (upper arm and forearm) carrying a small
payload at the hand. For every joint the torque is estimated in its worst-case static
pose, that is, with the arm stretched out horizontally so that every mass has the longest
possible lever arm about the joint. Three contributions are then added:

1. **Static torque** – holding the links, the arm-located servos and the payload against gravity.
2. **Dynamic torque** – accelerating the same masses from rest at a chosen angular acceleration.
3. **Friction margin** – a factor on the sum to cover friction and other unmodelled losses, as well as to have some design margin.

The total required torque is therefore given by Equation (1):

$$
\tau_{req} = SF_{fric}\,\left(\tau_{static} + \tau_{dyn}\right) \tag{1}
$$

### Joints and worst-case poses

Table 1 summarizes the arm joints, their motions, and the worst-case poses used for the calculations:

<div align="center" markdown="1">

| Joint | Motion | Worst-case pose used |
|:---:|:---:|:---:|
| J1 | Shoulder pitch | Arm straight and horizontal, pointing forward |
| J2 | Shoulder roll | Arm straight and horizontal, out to the side (T-pose) |
| J3 | Upper-arm rotation (yaw) | Elbow bent 90°, forearm horizontal |
| J4 | Elbow flexion | Forearm horizontal |

*Table 1: Arm joints, motions, and worst-case poses.*

</div>

J1 and J2 see the same load (the whole arm at full reach), and so do J3 and J4 (the forearm
and payload at full reach), so there are only two torque cases to calculate.

Apart from the arms, the head has two joints of its own: JN1 and JN2, for pan and tilt. With
four joints in each arm and two in the head, the robot has ten servos in total.

### Inputs

A table with the most relevant parameters for the calculations is provided in Table 2:

<div align="center" markdown="1">

| Symbol | Meaning | Value | Unit |
|:---:|:---:|:---:|:---:|
| $L_1$ | Upper-arm length (shoulder to elbow) | 0.12 | m |
| $L_2$ | Forearm length (elbow to hand) | 0.08 | m |
| $d_{J3}$ | Distance from the shoulder to the J3 servo | 0.05 | m |
| $m_{load}$ | Payload at the hand | 0.030 | kg |
| $m_{fa}$ | Forearm link mass | 0.0227 | kg |
| $m_{ua}$ | Upper-arm link mass | 0.0340 | kg |
| $m_{J3}$, $m_{J4}$ | Servo mass at J3 and at the elbow | 0.060 | kg |
| $g$ | Gravity | 9.81 | m/s² |
| $\alpha$ | Angular acceleration | 2 | rad/s² |

*Table 2: Calculation input parameters.*

</div>

The link masses are not yet measured. Each link is modelled as a hollow printed PLA tube with
outer diameter $D_o = 5$ cm, inner diameter $D_i = 4.7$ cm (1.5 mm wall) and density
$\rho = 1.24$ g/cm³, as expressed in Equation (2):

$$
m_{link} = \rho \, \frac{\pi}{4} \left(D_o^2 - D_i^2\right) L \tag{2}
$$

This gives about 23 g for the forearm and 34 g for the upper arm.

!!! note
    These are bare-tube masses. Brackets, infill and fasteners are not included, so the
    real links will be heavier. Part of this is offset by the friction margins.

### Static torque

The payload and the servos are modelled as point masses in which each link's weight acts at its mid-point.

**Elbow (J4) and upper-arm rotation (J3)**

The static torque for J3 and J4 is calculated using Equation (3):

$$
\tau_{J4} = m_{load}\, g\, L_2 + m_{fa}\, g\, \frac{L_2}{2} \tag{3}
$$

The individual static torque contributions for J3 and J4 are listed in Table 3:

<div align="center" markdown="1">

| Contribution | Lever arm | Torque (N·m) |
|:---:|:---:|:---:|
| Payload | $L_2$ | 0.0235 |
| Forearm | $L_2/2$ | 0.0089 |
| **Total J3, J4** | | **0.0324** |

*Table 3: Static torque breakdown for J3 and J4.*

</div>

**Shoulder (J1 and J2)**

The static torque for J1 and J2 is calculated using Equation (4):

$$
\tau_{J2} = m_{load}\, g\, (L_1 + L_2) + m_{fa}\, g \left(L_1 + \frac{L_2}{2}\right)
          + m_{J4}\, g\, L_1 + m_{ua}\, g\, \frac{L_1}{2} + m_{J3}\, g\, d_{J3} \tag{4}
$$

The individual static torque contributions for J1 and J2 are listed in Table 4:

<div align="center" markdown="1">

| Contribution | Lever arm | Torque (N·m) |
|:---:|:---:|:---:|
| Payload | $L_1 + L_2$ | 0.0589 |
| Forearm | $L_1 + L_2/2$ | 0.0356 |
| Elbow servo | $L_1$ | 0.0706 |
| Upper arm | $L_1/2$ | 0.0200 |
| J3 servo | $d_{J3}$ | 0.0294 |
| **Total J1, J2** | | **0.2145** |

*Table 4: Static torque breakdown for J1 and J2.*

</div>

The servos and the payload, not the printed links, make up most of the shoulder torque:
the elbow servo alone is a third of it.

### Dynamic torque

The torque needed to accelerate the arm is $\tau_{dyn} = I\,\alpha$, with $I$ the moment of
inertia of everything downstream of the joint, taken about the joint axis. Point masses
contribute $m r^2$ and a link rotating about its own end contributes $\tfrac{1}{3} m L^2$.

**Elbow (J4) and upper-arm rotation (J3)**

The moment of inertia for J3 and J4 is given by Equation (5):

$$
I_{J4} = m_{load}\, L_2^2 + \tfrac{1}{3}\, m_{fa}\, L_2^2 \tag{5}
$$

**Shoulder (J1 and J2)**

The moment of inertia for J1 and J2 is given by Equation (6):

$$
I_{J2} = m_{load}\,(L_1 + L_2)^2 + m_{fa} \left(L_1 + \frac{L_2}{2}\right)^2
       + m_{J4}\, L_1^2 + \tfrac{1}{3}\, m_{ua}\, L_1^2 + m_{J3}\, d_{J3}^2 \tag{6}
$$

The forearm is treated here as a point mass at its mid-point; its inertia about its own
centre is small by comparison and is neglected.

Table 5 presents the resulting moments of inertia and dynamic torques:

<div align="center" markdown="1">

| Joints | $I$ (kg·m²) | $\tau_{dyn}$ at 2 rad/s² (N·m) |
|:---:|:---:|:---:|
| J3, J4 | 0.00024 | 0.0005 |
| J1, J2 | 0.00296 | 0.0059 |

*Table 5: Moments of inertia and dynamic torques.*

</div>

At this acceleration the dynamic term is under 3 % of the static one: the sizing is
dominated by holding the arm against gravity.

### Required torque

Servo data sheets quote stall torque in kg·cm, so the results are converted with
1 N·m = 10.2 kg·cm. The friction margin used is $SF_{fric} = 1.5$. Table 6 summarizes the resulting required torques:

<div align="center" markdown="1">

| Joints | Static (N·m) | Dynamic (N·m) | Sum (N·m) | Sum (kg·cm) | With margin 1.5 (kg·cm) |
|:---:|:---:|:---:|:---:|:---:|:---:|
| J3, J4 | 0.0324 | 0.0005 | 0.0329 | 0.34 | **0.50** |
| J1, J2 | 0.2145 | 0.0059 | 0.2204 | 2.25 | **3.37** |

*Table 6: Summary of static, dynamic, and required torques.*

</div>

### Comparison with the servo candidates

The preferred architecture uses ten servos of two sizes: the larger
one for shoulder pitch and roll, the smaller one for upper-arm rotation, elbow flexion and
the head. Table 7 compares the servo candidates with the required joint torques:

<div align="center" markdown="1">

| Servo | Stall torque (kg·cm) | Joints | Required (kg·cm) |
|:---:|:---:|:---:|:---:|
| Dynamixel XL430-W250-T | 15.3 | J1, J2 | 3.37 |
| Dynamixel XL330-M288-T | 5.3 | J3, J4, JN1 , JN2 | 0.50 |
| STS3215-C044 | 16.0 | J1, J2 | 3.37 |
| STS3032 | 4.5 | J3, J4, JN1 , JN2 | 0.50 |

*Table 7: Comparison of candidate servos with required joint torques.*

</div>

The head joints are not part of this calculation, and are assumed within a similar range of
torques as the smallest motors. They will use the same servos as the rest of the robot.

!!! warning
    Due to availability issues current design only uses STS3215-C044 motors.The final build will use the STS3215-C044 for all ten joints. As an open option for the future, the STS3032 could replace it in J3, J4 and the head joints.
