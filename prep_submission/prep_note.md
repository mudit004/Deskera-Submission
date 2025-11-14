# Factorio Prep Notes

- *Player name:*  Mudit Mangal
- *Game version:* (from pause overlay)  : 2.0.72
- *Seed (daily seed):*  Tutorial 5
- *Playtime shown in save:*  
- *Mods:* None

## Mini‑challenge results

- *Max items/min on one yellow belt:* 900 items/min  
  Reference: base is 15 items/s total = 900 items/min (7.5/s per lane = 450/min).

- *Target: 120 green circuits/min*  
  - Iron plates required: *120/min*  
  - Copper plates required (for cables): *180/min*
  - My measured rates (10‑min Production graph):
    - Iron plates: 300/min
    - Copper plates: 219/min
    - Electronic circuits: 136/min

## One bottleneck and the fix
- Bottleneck: The amount of coal being mined was much higher than required, which frequently choked the steel production lanes and caused an imbalance between coal and iron plate consumption. Similarly, the number of electronic circuits being produced was higher than needed, leading to congestion in the production lines connected to the solar panel plant.
- Fix: To fix this, I reduced the number of coal mines and increased the number of iron furnaces to balance the production of iron plates with coal usage. For the circuit congestion, I split the output line, one line supplied the solar panel production plant, while the other diverted excess circuits into steel boxes. This prevented the lines from getting backed up and kept production running smoothly.

## One simplification that cleaned up the layout
- Simplification: I organized the smelting area in a way that furnaces were placed on both sides of the output lane, each having its own dedicated input lane for faster production. I also used splitters and underground belts to prevent congestion and maintain smooth material flow. Additionally, I kept all furnaces on one side of the map, which made the layout more organized and easier to manage.
---

## Quick math & ratios (for planning)

### **Yellow Belt Throughput**

* **Total (both lanes):** 15 items/s = **900 items/min**
* **Per lane:** 7.5 items/s = **450 items/min**

---

### **Smelting (Iron/Copper Plates)**

| Furnace Type   | Crafting Speed | Recipe Time (s) | Output (plates/min) |
| -------------- | -------------- | --------------- | ------------------- |
| Stone Furnace  | 1.0            | 3.2             | **18.75**           |
| Steel/Electric | 2.0            | 3.2             | **37.5**            |

---

### **Green Circuit Production**

**Recipe:**
1 × Iron Plate + 3 × Copper Cable → 1 × Electronic Circuit (0.5 s, crafting speed 1)

#### **Material Requirements for 120 circuits/min**

* **Iron Plates:** 120 plates/min
* **Copper Plates:** 180 plates/min (to make 360 cables/min)

#### **Assembler Calculations**

| Assembler Type | Crafting Speed | Circuit Output (items/min) | Cable Output (items/min) | Suggested Setup                                                                  |
| -------------- | -------------- | -------------------------- | ------------------------ | -------------------------------------------------------------------------------- |
| Assembler 1    | 0.5            | 60 circuits/min            | 120 cables/min           | **2 Circuit AM1 + 3 Cable AM1**                                                  |
| Assembler 2    | 0.75           | 90 circuits/min            | 180 cables/min           | **2 Cable AM2 + 2 Circuit AM2 (slightly overproducing)** or throttle for balance |

## Coordinates & seed
- Minimap with grid/coords: open map (M) → enable grid → screenshot.  
- Seed: show on *Load Game* screen at the end of your recording.