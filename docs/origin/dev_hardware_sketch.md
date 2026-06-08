# Dev Hardware Sketch

Purpose: define a coherent and complete development hardware platform that uses final-candidate hardware.
Development concessions are larger PCB area, headers, test points, jumpers, current monitors, configurable power rails, and external cabling. The development platform should otherwise be a full fidelity match for the final glasses design.

This document is hardware-only: BOM skeleton, subsystem partitioning, candidate ICs, interfaces, and audit order.

## 0. Dev Hardware Target

The V0 hardware target is composed of four parts as follows:

The final glasses-side hardware is split into
- A 3D-printed glasses/head frame with cameras, IMU, microphones, speakers, GNSS, display module, touch/control surfaces, and thermal sensors, placed where they would plausibly live in the final product.

- A larger off-glasses endpoint electronics board carrying the same class of SoC, memory, power tree, radios, FPGA/co-processor, and debug instrumentation that the final glasses electronics would use.

The final SDC-side hardware is split into
- The SDC SOM itself - Jetson Orin NX/Nano or SpacemiT K3-CoM260
- The SOM carrier board for product-specific SDC functions: LoRA/FLRC, power system, peripherals, 5G/eSIM networking, mass storage.

Primary selection metrics used to elect candidate hardware in the rest of this document:

1. Power optimization.
2. COTS availability.
3. Package size.

## 1. Master-Document Hardware Constraints

The master document and revised target imply these hardware constraints:

- Glasses-only target assumes roughly 0.9-1.2 Wh in glasses, with sustained glasses-side dissipation ideally below 1-2 W. The endpoint board can be larger for development, but component choices should still be power- and package-realistic.
- Ambient sensing must support low-power frame/event feeds before full-fidelity color video feed. HM0360-class low-power vision, single-eye tracking, IMU, and microphone wake paths route through the low-power island first.
- Rich display sessions, texture loads, full video streaming, and other high-bandwidth SDC-to-glasses traffic use Wi-Fi. LR2021/FLRC is the outbound low-power telemetry path.

## 2. Physical Partition

| Assembly | Contains |
|---|---|
| Glasses Frame | 3D-printed frame, cameras, IMU, mics, GNSS receiver/antenna, speaker transducers, display module, ALS/prox/wear sensors, temp sensors, touch/button surfaces |
| Endpoint Dev Board | i.MX 8M Mini, LPDDR4, small QSPI/FlexSPI NOR, DNP/debug eMMC fallback, PMIC, one or two GW1NZ-2-class streaming helpers, LR2021, Wi-Fi/BT, power instrumentation |
| SDC SOM | COTS Jetson Orin NX/Nano or SpacemiT K3-CoM260 compute module |
| SDC Carrier | SDC enclosure, pocket box form factor, SOM power, mass storage, LR2021 peer, dedicated glasses Wi-Fi AP, separate upstream Wi-Fi client/ETH/5G/eSIM networking, USB-C PD, peripheral expansion |

## 3. Endpoint Electronics Board BOM

| Subsystem | Primary part / class | Status | Why this is the default | Audit notes |
|---|---|---|---|---|
| Application SoC | NXP i.MX 8M Mini Solo/Dual, GPU+VPU, 14 x 14 mm FCBGA | Core | Same package class as GPU-capable Nano while adding 1080p60 H.264 encode, display, CSI, audio, Ethernet MAC, USB, SDIO, and PCIe | Mini Solo `MIMX8MM2` and Mini Dual `MIMX8MM4` are the attractive endpoint SKUs: 1x/2x A53, Cortex-M4, GPU, VPU. |
| SoC PMIC | NXP PCA9450B | Core | Companion PMIC for i.MX 8M Nano/Mini family | Start from NXP EVK/reference design, then add measurement, rail jumpers, standby rails, and DVS policy. |
| DRAM | Winbond W66BP6NBHAFJ, 2Gb/256MB LPDDR4, x16, 100-VFBGA 10 x 7.5 mm | Core | Small package | Start with one x16 device on the minimum viable bus. Add a second x16 device or fall back to Kingston D1621PM4CDGVIW-U / ESMT M56Z16G32512A-SMBG x32 10 x 14.5 mm class only if VPU/GPU/display buffers prove the smaller topology too tight. |
| Boot/storage | Winbond W25Q64PWXHIQ, 64Mbit/8MB 1.8 V Quad SPI/QPI NOR, XSON-8 2 x 3 mm | Core | Small NOR avoids eMMC idle/power/bring-up overhead | Connect to FlexSPI/QSPI boot path. Use deep-power-down in endpoint sleep. Keep eMMC or larger NOR only as DNP/debug fallback if measured firmware images outgrow 8MB. |
| Control core | i.MX 8M Mini Cortex-M4 | Core | M4 can own IMU, mic wake, power policy, FPGA control, LR2021 TX scheduling, and A53 mailbox inside endpoint power states | Verify IDLE/SUSPEND power, bonded GPIO, MICFIL/PDM ownership, SPI/I2C/GPIO access, MU mailbox, and wake latency. |
| Motion sensing | ICM-45686 6-axis baseline; BHI360 + BMM350-class smart 9DoF audit path | Core | 6-axis covers low-power motion telemetry; 9DoF requires on-sensor fusion output | Keep magnetometer placement away from speakers, display magnets, charging current, and steel fasteners. Compare fused heading current against 6-axis plus vision correction. |
| Audio capture | 2-4 T5838-class PDM microphones | Core | AAD wake and low-power PDM modes support always-listening audio without waking the full SoC | Keep one AAD wake mic always available; clock-gate and load-switch the full array for richer capture. |
| Lowfi FPGA helper | GOWIN GW1NZ-2 | Power-win candidate | Very small helper for HM0360 stream conditioning and deterministic telemetry formatting | Populate after measured energy per useful frame beats the M4/A53 implementation. Codec scope stays raw/tile/minimal. |
| Eye hint sensor | Himax HM01B0 | Primary eye sensor audit | Commodity low-res always-on vision sensors with low-power modes and 1/4/8-bit digital-video output options | Pick lowest useful rate/ROI. Target camera-space pupil/blob hints, not image quality. |
| Eye sparse helper | Second GW1NZ-2-class part | Candidate | Extracts camera-space pupil/blob/glint/blink/confidence tuples from the inward-eye camera | Internal registers/BRAM only. Sensor interface must be GW1NZ-friendly or use a tiny bridge. Outputs sparse lower-rate features to the telemetry FIFO for SDC-side fusion. |
| Head-frame interconnect | FPC bundle | Core | Keeps head-frame placement real while endpoint board stays large | Split by interface class: high-speed MIPI/display, low-speed sensor/control, audio, power/ground, GNSS host/control/power, and debug spares. GNSS RF path stays local to the frame. |
| Camera routing | Good color camera owns i.MX CSI/VPU; HM0360 to lowfi helper; eye camera to eye sparse helper | Core | Keeps rich color encode, lowfi world telemetry, and sparse eye telemetry on separate paths | Add mux/header access for raw calibration capture and camera path comparisons. |
| Endpoint SDIO Wi-Fi | Murata Type 2EL / NXP IW612 first; TI CC3351MOD and Murata Type 2GY as audit comparators | Core | Handles high-bandwidth SDC-to-glasses RX and host networking for encoded stream traffic | Selection is measured associated-idle, DTIM/TWT behavior, RX latency, Linux/i.MX support, 1.8 V I/O, antenna path, and module availability. |
| Lowfi telemetry radio | Semtech LR2021 | Core | Power-optimized FLRC/LoRa outbound world/eye/motion telemetry | Product mode is TX-only from glasses to SDC. M4/reserve MCU owns radio state; FPGA supplies payloads. |
| Low-bandwidth command RX | nRF54L15 / Type 2NR BLE first for always-on command RX; IW612 BT as integration fallback | Core experiment | SDC-to-glasses command bands, wake, pairing, provisioning, policy updates | Select by connected-average current at target interval, wake latency, coexistence, and firmware control. Rich graphics assets, texture loads, and video use Wi-Fi. |
| Secure identity | NXP SE050C or Microchip ATECC608C | Optional V0, likely final | Device identity, pairing, provisioning, and audit roots | Reserve footprint. |
| Power instrumentation | INA226/INA231/INA228-class monitors, sense-resistor bypasses, rail jumpers | Core dev | Per-rail telemetry drives FPGA, VPU, radio, and A53 decisions | Make measurement removable/bypassable for final-like power runs. |
| Switching rails | TPS62840/TPS62843-class nano-IQ bucks plus load-specific higher-current bucks where needed | Core | Use switching conversion for material loads and choose rail voltages close to each load domain | Measure light-load efficiency, burst efficiency, transient behavior, inductor DCR, and forced-PWM noise. |
| Noise-cleanup LDOs | TPS7A02/TPS7A03/TPS7A20-class post-buck LDOs; LT3045-class lab footprint for sensitive analog only | Core audit | LDOs clean rails after efficient buck conversion where voltage drop and load current are small | Budget `P = (Vin - Vout) * Iload`; each LDO needs a measured noise or PSRR win. |
| Power switching | TPS22916/TPS22919-class load switches | Core | Gate display, cameras, FPGA rails, LR2021, Wi-Fi, audio, sensors, VPU-related rails, and debug sections separately | Select for leakage, on-resistance, inrush control, package, and default-off behavior. |
| Battery path | BQ25155/BQ25180-class 1S wearable charger/power path + MAX17262-class fuel gauge | Optional V0 | Runtime characterization after bench-powered board works | Prioritize ship-mode current, battery-only quiescent current, power-path behavior, charge-current range, thermistor support, and fuel-gauge operating current. |
| Debug/recovery | USB 2.0 OTG, UART console, JTAG/SWD, FPGA JTAG, boot strap headers | Core | Board recovery while firmware, FPGA, VPU pipeline, and radios are unstable | Keep all debug paths physically accessible. |

## 4. Low-Power Island And FPGA

Programmable helpers earn BOM position through measured energy reduction over running the same function on M4/A53. The design ceiling is two GW1NZ-2-class streaming helpers using internal registers/BRAM and line/tile buffers.

```text
HM0360 ambient camera
  -> GW1NZ-2 lowfi stream helper
  -> M4/reserve MCU telemetry FIFO
  -> LR2021 TX-only telemetry

HM01B0 / HM0360 / HM0361 eye hint camera
  -> GW1NZ-2-class eye sparse helper
  -> camera-space pupil/blob/glint/blink/confidence tuples
  -> M4/reserve MCU telemetry FIFO
  -> LR2021 TX-only telemetry

A53 application side
  -> display, Wi-Fi, rich color camera, VPU encode, debug, calibration capture
```

| Function | First implementation | Helper admission test | BOM result |
|---|---|---|---|
| HM0360 minimum telemetry | M4/A53 software baseline plus GW1NZ-2 RTL power test | Same frame rate, same latency target, lower energy per useful telemetry frame | GW1NZ-2 populated for a measured win. |
| HM0360 quality tiers | Raw/tile/minimal codec inside GW1NZ-2 budget | Fits 2k LUT4 class with small buffers and deterministic packet timing | Codec scope stays small. |
| Eye sparse features | Second GW1NZ-2-class streaming helper | Threshold/blob/centroid/glint/confidence extraction fits internal buffers and beats A53 energy | Camera-space sparse telemetry joins HM0360 stream for SDC-side fusion. |
| Two-helper ceiling | Lowfi helper plus eye sparse helper | Both helpers fit rail, package, routing, clocking, and telemetry budgets | Maximum FPGA class is GW1NZ-2-class. |
| Rich color-video compression | i.MX 8M Mini VPU | VPU power, latency, quality, and camera path behavior beat software encode | FPGA codec scope stays lowfi. |

Recommended FPGA direction:

1. Default programmable-helper BOM is one GW1NZ-2 for HM0360 telemetry.
2. Eye tracking uses a separate GW1NZ-2-class sparse feature subsystem when it beats the A53 energy path.
3. Eye output is camera-space pupil/blob/glint/blink/confidence telemetry.
4. SDC performs screen-space fusion with lowfi world telemetry and calibration state.
5. Lowfi codec work stays raw/tile/minimal; rich color video uses the Mini VPU.

## 5. Endpoint Data Paths

### Lowfi Telemetry Path

```text
HM0360
  -> GW1NZ-2 stream helper
  -> M4/reserve MCU packet policy
  -> LR2021 TX-only telemetry
  -> SDC carrier LR2021 peer
```

GW1NZ-2 participates after a measured power win over M4/A53 for the exact lowfi tier.

### Eye Tracking Path

```text
HM01B0 / HM0360 / HM0361 inward-eye camera
  -> GW1NZ-2-class eye sparse helper
  -> camera-space pupil/blob/glint/blink/confidence tuples
  -> M4/reserve MCU packet policy
  -> LR2021 TX-only telemetry
  -> SDC fusion with lowfi world stream
```

The glasses-side eye subsystem emits sparse camera-space features. SDC owns screen-space mapping, calibration fusion, and higher-order gaze inference.

### Rich Color Video Encode Path

```text
VD65G4 / Mira220 / AR0234-class color global-shutter sensor
  -> i.MX 8M Mini CSI
  -> i.MX 8M Mini VPU H.264 bitstream
  -> Wi-Fi or debug Ethernet
  -> SDC
```

Mini becomes the rich-color-video baseline because it adds VPU encode inside the same 14 x 14 mm package class being selected for GPU.

### Display And High-Bandwidth RX

```text
SDC
  -> Wi-Fi
  -> i.MX A53 application side
  -> GPU/display controller
  -> MIPI DSI display module
```

Graphics assets, textures, full video streaming, and rich session state are Wi-Fi traffic. BLE/control carries low-bandwidth command bands after latency and power measurement.

## 6. Head-Frame BOM Skeleton

The head frame carries final-ish physical placement. The endpoint board can be large; the head-mounted geometry should stay realistic.

| Location | Hardware | Notes |
|---|---|---|
| Front/world-facing | HM0360 module | Place for intended ambient FOV.|
| Front/world-facing | VD65G4 / Mira220 / AR0234-class color module | Final-ish optical axis, lens choice, FPC routing, and calibration fiducials. |
| Display-eye inward side | HM01B0/HM0360/HM0361 eye hint camera | Place for pupil/blob visibility through expected eye box; optimize for low rate, low bandwidth, and low power. |
| Display-eye inward side | IR illumination reserve | 1-2 low-current 850/940 nm emitters or DNP pads. Benchmark ambient/display-lit eye hints first, then low-duty illumination with simple PWM/current control. |
| Temple/bridge rigid reference | ICM-45686 6-axis IMU baseline; BHI360 + BMM350-class 9DoF/fusion audit pads | Mechanically isolate from cable tug and frame flex. Route to M4/reserve control core first. If 9DoF is installed, consume fused sensor-hub output rather than doing glasses-side software fusion. |
| Temples/front | 2-4 T5838-class PDM mics | Acoustic ports, wind path, spacing, and symmetry matter. Keep AAD wake path available and switch/clock richer array modes by policy. |
| Outer temple / frame edge | GSGL-0003 GNSS receiver + GNSS antenna keepout | Place for sky view, stable ground reference, and separation from Wi-Fi, display FPC, speakers, and high-current switching loops. Keep antenna feed and RF matching local to the frame. |
| Temples | Open-ear speakers/transducers | Include acoustic volume, sealing, leakage, and comfort experiments. |
| Eye/display side | OP03011/JBD/OEM display module | Real MIPI FPC, mechanical alignment, brightness current sense, and thermal path. |
| Frame/user-facing | ALS/prox/wear sensors | Display power policy, wake, wear detection, and privacy behavior. |
| Temples/skin proxy | TMP117/NTC sensors | Measure skin-side and electronics-side temperature separately. |
| Temple surface | Touch strip | Final-ish reach, haptics/feedback assumptions, and sealed routing. |
| Cable set | FPC bundle | Cameras and display. |
| Cable set | Low-speed FPC/wire harness | IMU, mics, GNSS I2C/SPI plus enable/reset/backup/main power, ALS/prox, temp, touch, IR illumination control, power, ground. |
| Cable set | GNSS local RF | Antenna, matching network, keepout, and RF test point stay on the glasses frame; do not route GNSS RF back to the endpoint board. |

## 7. SDC SOM Options

| SOM option | Status | Why use it | Carrier implications |
|---|---|---|---|
| NVIDIA Jetson Orin NX | Primary AI/pro candidate | Strong local AI/vision ecosystem, CUDA/TensorRT, mature SOM path | Carrier needs NVMe, power/thermal margin, high-speed networking, radios, and clean recovery/debug. |
| NVIDIA Jetson Orin Nano | Lower-power/lower-cost Jetson-compatible candidate | Same 260-pin SO-DIMM carrier direction as Orin NX; useful for lower power/cost SDC characterization | Same carrier family as Orin NX. |
| SpacemiT K3 / K3-CoM260 | Jetson Orin Nano/NX pin-compatible RISC-V alternate | Preserves the Jetson carrier-board investment while testing a different CPU/AI/software stack | Audit software maturity, availability, BSP quality, and power/thermal behavior. |
| Other SOMs | Track | RK3588, x86 embedded, or Qualcomm modules may be useful later | Keep endpoint architecture independent of SDC SOM choice. |

## 8. SDC Carrier BOM Skeleton

Design the SDC carrier from the 260-pin SO-DIMM interface budget first. M.2 sockets are endpoint allocations of PCIe/USB/control pins, not free expansion slots.

### SO-DIMM Interface Budget

| Interface group | What the SO-DIMM family exposes | Carrier allocation |
|---|---|---|
| PCIe total | Up to seven carrier lanes: PCIE0 x4, PCIE1 x1, PCIE2 x2 or PCIE2/PCIE3 split x1/x1 | x4 NVMe, x1 soldered glasses AP, x1 soldered upstream Wi-Fi client, x1 optional M-key mobile roaming. |
| Primary PCIe | PCIE0 x4, Nano Gen3 / NX Gen4 | One M.2 Key M NVMe slot for storage. |
| Secondary PCIe | PCIE2/PCIE3 split x1/x1 mode | Soldered upstream Wi-Fi client plus optional M-key mobile roaming module. |
| Tertiary PCIe | PCIE1 x1 | Soldered glasses AP radio. |
| USB 3.x | Up to three SuperSpeed ports with UPHY sharing | USB-C recovery/debug plus one hub/root path for lab USB and mobile roaming control/debug functions. |
| USB 2.0 | Multiple UTMI-style ports, also used by radio Bluetooth/control functions | Pair with soldered radios, mobile endpoint control, and USB hub/device functions. |
| Ethernet | Integrated GbE PHY MDI pairs from the SOM | Carrier magnetics, RJ45, LEDs, and optional PoE header. |
| Display/camera | DP/eDP and CSI lanes exposed by carrier reference designs | Bring out only if useful for SDC debug or sensor experiments. |
| Low-speed control | UART, SPI, I2C, I2S, GPIO, fan, buttons, recovery | LR2021 peer, power controls, debug header, fan, buttons, LEDs. |

### Reference Carrier Allocation

| Carrier endpoint | SO-DIMM budget consumed | BOM decision |
|---|---|---|
| M.2 Key M 2280 | PCIe x4 primary path | Populate for NVMe. |
| Soldered AP radio | PCIe x1 plus USB2/UART/I2S/I2C/control | Glasses private link. |
| Soldered upstream Wi-Fi client | PCIe x1 plus USB2/UART/control | Roaming WLAN client. |
| Optional M.2 Key M mobile roaming | PCIe x1 plus USB2/USB3/SIM/eSIM control as needed | Cellular supplement |
| USB-C recovery/debug | USB2 plus one SuperSpeed path | Keep direct |
| USB host expansion | USB2/USB3 hub from one root path | Fan out through hub topology. |
| GbE RJ45 | Dedicated GbE MDI pins plus magnetics | Keep one wired debug/factory/network port. |

| Subsystem | Primary part / class | Status | Notes |
|---|---|---|---|
| SOM connector/power | Jetson Orin NX/Nano-compatible 260-pin SO-DIMM carrier implementation | Core | Supports Jetson Orin NX/Nano first and keeps SpacemiT K3-CoM260 in the same carrier family. |
| Primary storage | M.2 Key M NVMe SSD on x4 PCIe | Core | Boot, System, Files, Local world cache, logs, model storage, replay data. |
| Glasses Wi-Fi AP | Soldered Wi-Fi 6E/7 radio using one x1 PCIe plus USB2/control | Core | Private low-latency WLAN for glasses RX/TX, fixed channel planning, dedicated antennas, and SDC-controlled QoS. |
| Upstream Wi-Fi client | Soldered Wi-Fi 6E/7 client radio using one x1 PCIe plus USB2/control | Core | Roaming network capability, compartmentalized from the glasses AP. |
| Mobile roaming / eSIM | M.2 Key M module using one x1 PCIe lane, with USB/control and SIM/eSIM support | Optional | Supplements WLAN |
| LR2021 peer | Semtech LR2021 + RF front end on SPI/GPIO | Core | Receives endpoint lowfi telemetry and provides RF measurement baseline. |
| USB | USB-C recovery/debug, USB hub, debug UART, recovery controls | Core | Hub topology part of lane budget and SDC product hardware |
| Power | USB-C PD sink/source, battery input option, high-efficiency bucks, fuel gauge | Core | SDC power is separate from glasses power and still portable-oriented. |
| Thermal | Heatsink/fan or passive spreader depending SOM | Core | Treat as SDC product hardware. |
| Expansion | spare SPI/I2C/UART/GPIO, camera/debug headers | Core support | Low-speed access for LR2021, test fixtures, and board control. |

## 9. Later Audit Items

| Item | Next action |
|---|---|
| Rich color-video encode | Bench i.MX 8M Mini VPU with the intended camera modes and network paths. |
| LR2021 airtime | Keep endpoint airtime budget focused on outbound telemetry; test BLE/Wi-Fi command paths separately. |
| Production optical engine | Use OEM display module first while preserving final-ish placement and FPC constraints. |
| Production battery pack | Start bench-powered with final-like rails and measurement; add protected 1S later. |
| Final FPGA topology | Choose one GW1NZ-2 helper or two GW1NZ-2-class helpers from measured energy and BOM cost. |
| Good color camera | Compare VD65G4, Mira220 RGB/RGBIR, and AR0234-class modules for image quality, power, package, lens stack, and i.MX Mini bring-up friction. |
| Eye camera interface | Audit HM01B0 first, HM0360/HM0361 second, then OV7251/OVM7251, ARX3A0/ARX383, OC0TC, and Mira016 for helper-friendly output, power, package, lens/IR geometry, and bridge cost. |
| Eye illumination | Compare ambient/display-lit operation, low-current DC IR, and low-duty synchronized IR pulses for feature confidence per milliwatt. |
| Motion sensing | Compare ICM-45686 6-axis baseline against BHI360 + BMM350-class built-in-fusion 9DoF path for heading value per milliwatt. |
| Microphone path | Measure one-mic AAD wake, low-power PDM capture, and full-array capture separately. |
| Endpoint power tree | Lock buck setpoints, load-switch groups, post-buck LDO cleanup drops, charger/fuel-gauge path, and measurement bypasses from efficiency data. |
| Endpoint SDIO Wi-Fi / BLE | Compare IW612/Type 2EL, CC3351MOD, Type 2GY, nRF54L15, and Type 2NR for low-power associated behavior, command RX latency, host support, and availability. |

## 10. Immediate Audit Order

1. Confirm exact i.MX 8M Mini SKU: Solo/Dual preferred, GPU+VPU enabled, 14 x 14 mm, temp grade, speed bin, package availability.
2. Build the Mini rich-color-video baseline: VD65G4/Mira220/AR0234-class CSI ingress, VPU H.264 settings, latency, quality, power, thermal rise, Wi-Fi/debug-Ethernet egress.
3. Lock camera partition: rich color camera to Mini CSI/VPU, HM0360 to lowfi helper, inward-eye camera to sparse eye helper.
4. Build the GW1NZ-2 lowfi benchmark: HM0360 ingress, deterministic frame skip, tile/ROI counters, timestamps, packet framing.
5. Measure GW1NZ-2 energy per useful HM0360 telemetry frame against M4/A53 software handling.
6. Build the eye sparse helper benchmark: inward-eye ingress, thresholding, blob/centroid or ellipse estimate, glint candidates, blink/confidence, lower-rate packetization.
7. Measure second-helper energy per useful eye feature tuple against A53 extraction.
8. Confirm both helpers fit internal registers/BRAM, rail, clock, routing, and LR2021 payload budgets.
9. Pull NXP EVK/reference design and lock the minimum SoC support set: PCA9450B, smallest viable LPDDR4 topology, W25Q64PW-class QSPI/FlexSPI NOR, DNP/debug eMMC fallback, clocks, boot straps, JTAG/UART.
10. Draft endpoint power tree: switching rail setpoints, load switches, post-buck LDO cleanup drops, charger/fuel-gauge path, and measurement bypasses.
11. Prove M4 control-core viability: IDLE/SUSPEND power, bonded GPIO, MICFIL/PDM ownership, SPI/I2C/GPIO access, MU mailbox, wake latency.
12. Benchmark motion/audio/radio low-power paths: ICM-45686, BHI360+BMM350-class fusion, T5838 AAD/PDM, SDIO Wi-Fi, and BLE command RX.
13. Lock head-frame sensor/GNSS placement, GNSS antenna keepout, and FPC pinout assumptions before endpoint schematic work.
14. Select good-camera procurement path: VD65G4 first for tiny low-power RGB global shutter, Mira220 RGB/RGBIR for higher-resolution global shutter, AR0234-class module for mature 2MP bring-up comparison.
15. Select eye camera/illumination path: HM01B0 first, HM0360/HM0361 second, OV7251/ARX3A0-class only if their imaging value beats bridge/interface cost, optional 850/940 nm emitter pads, minimal PWM/current control, eye-safety limits.
16. Lock LR2021 as TX-only endpoint telemetry in product mode and define SDC carrier peer/test hardware.
17. Choose command RX path: discrete nRF54L15/Type 2NR BLE first, with IW612 BT as integration fallback.
18. Choose SDC soldered Wi-Fi radios: glasses AP radio and separate upstream Wi-Fi client radio.
19. Draft SDC SO-DIMM lane budget: x4 NVMe, x1 glasses AP radio, x1 upstream Wi-Fi client, x1 optional M-key mobile roaming/eSIM, USB hub, GbE, LR2021 SPI/GPIO, and DNP high-speed alternatives.
20. Choose SDC SOM candidates to support on carrier rev A: Jetson Orin NX first, Jetson Orin Nano as the lower-power same-family option, and SpacemiT K3-CoM260 as the Jetson-pin-compatible RISC-V alternate.
21. Draft endpoint board block diagram and connector map.
22. Draft SDC carrier block diagram separately.

## 12. Sources Checked

- NXP i.MX 8M Nano product page and documentation: https://www.nxp.com/products/i.MX8MNANO
- NXP i.MX 8M Nano datasheet: https://www.nxp.com/docs/en/data-sheet/IMX8MNIEC.pdf
- NXP i.MX 8M Nano reference manual: https://www.nxp.com/docs/en/reference-manual/IMX8MNRM.pdf
- NXP i.MX 8M Mini product page and documentation: https://www.nxp.com/products/i.MX8MMINI
- NXP i.MX 8M Mini datasheet: https://www.nxp.com/docs/en/data-sheet/IMX8MMIEC.pdf
- NXP i.MX 8M Mini reference manual: https://www.nxp.com/docs/en/reference-manual/IMX8MMRM.pdf
- NXP i.MX 8M LPDDR4/DDR memory guide: https://community.nxp.com/t5/i-MX-Processors-Knowledge-Base/i-MX-8M-Quad-Mini-Nano-Plus-LPDDR4-DDR4-amp-DDR3L-memory/ta-p/1434761
- NXP PCA9450 PMIC: https://www.nxp.com/products/PCA9450
- Winbond customized memory guide, LPDDR4/4X package classes: https://www.winbond.com/export/sites/winbond/product-selection-guide/file/2026-Winbond-Customized-Memory-Solution.pdf
- Winbond W25Q64PW 1.8 V serial NOR: https://www.winbond.com/hq/product/code-storage-flash-memory/serial-nor-flash/?__locale=en&partNo=W25Q64PW
- ESMT M56Z16G32512A LPDDR4: https://www.esmt.com.tw/upload/pdf/ESMT/datasheets/M56Z16G32512A.pdf
- Himax HM01B0: https://www.himax.com.tw/products/cmos-image-sensor/always-on-vision-sensors/hm01b0/
- Himax HM0360: https://www.himax.com.tw/products/cmos-image-sensor/always-on-vision-sensors/hm0360/
- Himax HM0361: https://www.himax.com.tw/products/cmos-image-sensor/always-on-vision-sensors/hm0361/
- ams OSRAM Mira050: https://ams-osram.com/products/sensors/cmos-image-sensors/ams-mira050-cmos-image-sensor
- ams OSRAM Mira220: https://ams-osram.com/products/sensors/cmos-image-sensors/ams-mira220-cmos-image-sensor
- ams OSRAM Mira016: https://ams-osram.com/products/sensors/cmos-image-sensors/ams-mira016-cmos-image-sensor
- ST VD55G4 / VD65G4: https://www.st.com/en/imaging-and-photonics-solutions/vd55g4.html
- onsemi AR0234CS overview: https://www.onsemi.com/parametrics/AR0234CS/create-overview-pdf
- OMNIVISION OC0TC CameraCubeChip: https://www.ovt.com/products/oc0tc/
- OMNIVISION OV7251: https://www.ovt.com/products/ov7251/
- onsemi ARX3A0: https://www.onsemi.cn/products/sensors/image-sensors/ARX3A0
- GOWIN GW1NZ datasheet: https://cdn.gowinsemi.com.cn/DS841E.pdf
- NXP IW612: https://www.nxp.com/products/IW612
- Murata Type 2EL / IW612 module: https://www.murata.com/en-sg/products/connectivitymodule/wi-fi-bluetooth/overview/lineup/type2el
- Nordic nRF54L15: https://www.nordicsemi.com/Products/nRF54L15
- Murata Type 2NR / nRF54L15 module: https://www.murata.com/en-us/products/connectivitymodule/bluetooth/overview/lineup/type2nr
- TI CC3351 Wi-Fi 6/Bluetooth LE companion IC: https://www.ti.com/product/CC3351
- Murata Type 2GY Wi-Fi/Bluetooth module: https://www.murata.com/en-us/products/connectivitymodule/wi-fi-bluetooth/overview/lineup/type2gy
- Goertek GSGL-0003 GNSS module: https://www.digikey.com/en/products/detail/goertek-microelectronics-inc/GSGL-0003/23584829
- Quectel LC76G GNSS module: https://www.quectel.com/product/gnss-lc76g-series
- Semtech LR2021: https://www.semtech.com/products/wireless-rf/lora-plus/LR2021
- Microchip KSZ9131: https://www.microchip.com/en-us/product/ksz9131
- OMNIVISION OP03011: https://www.ovt.com/products/op03011/
- JBD 0.13 inch MIPI microLED display: https://www.jb-display.com/product_des/1.html
- TDK ICM-45686: https://invensense.tdk.com/products/motion-tracking/6-axis/icm-45686/
- Bosch BHI360 smart sensor: https://www.bosch-sensortec.com/products/smart-sensor-systems/bhi360/
- Bosch BMM350 magnetometer: https://www.bosch-sensortec.com/products/motion-sensors/magnetometers/bmm350/
- TDK T5838 PDM microphone: https://invensense.tdk.com/products/T5838
- TI TPS62840 nano-IQ buck: https://www.ti.com/product/TPS62840
- TI TPS62843 nano-IQ buck: https://www.ti.com/product/TPS62843
- TI TPS7A02 low-IQ LDO: https://www.ti.com/product/TPS7A02
- TI TPS7A03 low-IQ LDO: https://www.ti.com/product/TPS7A03
- TI TPS7A20 low-noise LDO: https://www.ti.com/product/TPS7A20
- TI TPS22916 load switch: https://www.ti.com/product/TPS22916
- TI TPS22919 load switch: https://www.ti.com/product/TPS22919
- TI BQ25155 wearable charger/power path: https://www.ti.com/product/BQ25155
- TI BQ25180 linear charger: https://www.ti.com/product/BQ25180
- Analog Devices MAX17262 fuel gauge: https://www.analog.com/en/products/max17262.html
- NVIDIA Jetson Orin module family: https://www.nvidia.com/en-us/autonomous-machines/embedded-systems/jetson-orin/
- NVIDIA Jetson Orin NX/Nano custom carrier bring-up docs: https://docs.nvidia.com/jetson/archives/r36.5/DeveloperGuide/HR/JetsonModuleAdaptationAndBringUp/JetsonOrinNxNanoSeries.html
- NVIDIA Jetson Orin Nano Developer Kit carrier board specification: https://developer.nvidia.com/downloads/assets/embedded/secure/jetson/orin_nano/docs/jetson_orin_nano_devkit_carrier_board_specification_sp.pdf
- SpacemiT K3 brief: https://cdn-resource.spacemit.com/file/chip/K3/K3_brief_en.pdf
- Banana Pi BPI-SM10 / K3-CoM260 docs: https://docs.banana-pi.org/zh/BPI-SM10/BananaPi_BPI-SM10
- Banana Pi BPI-SM10 / K3-CoM260 Jetson-compatible carrier note: https://forum.banana-pi.org/t/banana-pi-bpi-sm10-with-spacemit-k3-ai-chip-design/26657
- CNX Software K3-CoM260 / Jetson Orin Nano-NX carrier compatibility summary: https://www.cnx-software.com/2026/05/11/rva23-pico-itx-sbc-spacemit-k3-octa-core-risc-v-ai-soc-up-to-32gb-ram-256gb-ufs/
- Quectel RG520N 5G module: https://www.quectel.com/product/5g-rg520n-series/
- Telit Cinterion FN990B40 5G M.2 data card: https://www.telit.com/devices/fn990b40/
