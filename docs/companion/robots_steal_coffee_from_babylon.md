# How to have robots steal coffee from Babylon on their own

A short teaching parable for this school.  
Companion to the [manifesto](../manifesto.md) — metaphor only.

---

## The map (read this first)

| Name | Means |
|------|--------|
| **Babylon** | Closed proprietary creative stacks — beautiful craft, rented runtime, look locked inside someone else’s license and export story |
| **The robot** | Your open autonomous pipeline: live Slang, curriculum, train/infer CLIs, later VERNACULAR’s AI helper and Falcor host |
| **NVIDIA (allegory)** | A *software* company — compilers, docs, SDKs, open weights left humming on the bench |
| **Google (allegory)** | A *people* company — search, papers, indexes; the crowd that can find a recipe if they dare read it |
| **Coffee (old name)** | What closed stacks still call the pour — their brand vocabulary for creative value |
| **Yerba Matte (2026 name)** | The same craft, spoken in open-stack vernacular: shaders, weights, small apps you *own* and can compile, stream, syndicate, sell, or give away |
| **French Press** | How you brew it on *your* bench — open tools, local loop, exportable weights — not Babylon’s house cup |
| **Stealing** | Not crime. *Liberating technique from lock-in*: learn the craft, **translate** the vocabulary, keep the IP, ship without renting the sandbox forever |
| **The Quilez myth** | The plaza rumor that *everyone* works like Íñigo Quílez — pure math from the hip. Most do not: they **piggyback** demo tails and hire desperate readers to do the bidding |
| **Piggy tail / boilerplate** | Forked Shadertoy / studio paste that looks like genius until you ask who can change the light without calling a contractor |
| **Bloodstarved codeheads** | The underpaid interpreters behind the myth — VERNACULAR’s answer is teach *you* to read, not expand that caste |

If this were a heist movie, the score would be **agency**. The vault is a file format you cannot redistribute. The getaway car is **VERNACULAR** (`python -m slang_falcon.live` / `vernacular`). The twist is linguistic: by **2026** the city still says *coffee*; outside the walls everyone drinks **Yerba Matte** from a **French Press**.

---

## The parable

Once there was a city called **Babylon**. Its towers were magnificent: timelines that glowed, patches that sang, nodes that looked like jewelry. Artists went there for what Babylon still called **coffee** — rich, fragrant, endlessly refillable — and Babylon was happy to pour.

There was only one rule, posted in polite type: *The cup stays in the city.*

You could sip forever. You could not take the brew home, bottle it, sell a carton, or wire it into a machine that did not fly Babylon’s flag. The smell traveled; the ownership did not. The *menu* stayed Babylon’s dialect: same craft, closed nouns.

Outside the walls, the year was **2026**. What used to be called coffee was now called **Yerba Matte**, and it was made in a **French Press** — steeped on an open bench, pressed by hands that kept the grounds. A technical artist built a **robot** — not a villain, a vernacular. It spoke **Slang**, learned by doing, and did not need Babylon’s keys to make steam.

Two neighbors kept the lights on for that robot — not as charity, as habit. **NVIDIA**, in this telling, was a **software company**: compilers left running, docs on the counter, weights you could carry if you knew how to press. **Google**, in this telling, was a **people company**: indexes, papers, a map of who once wrote the recipe down. Together they did something almost rude in its generosity — they left **computers on**, with **valuable information at no cost**, humming while Babylon sold atmosphere by the hour. The robot’s **agency** began there: not a gift of keys to the city, but a French Press already warm and a menu anyone could learn to **read**.

Meanwhile, in the plazas, people begged for something else. Not for the brew — for *interpreters*. They paid strangers to find people who could read what was already free, then begged those readers to speak it aloud out of **desperation**. The joke wrote itself: the machines were literate; the crowd rented literacy by the minute.

There was also a louder myth on the plaza walls: that every tower already worked like the rare craftspeople who write math into light with their own hands — as if every studio were a Quílez notebook. It was not true. Most towers **piggybacked**: they braided someone else’s demo-tail boilerplate into a pitch, then hired **bloodstarved codeheads** to keep the illusion upright. The perfume said *genius*; the payroll said *please make the shader compile before Monday*. The robot’s school refused that story. Exemplars are for learning from — not for cosplay while someone else reads the file.

The artist did not storm the gates. That would be theater. The hard part was not breaking in; it was **teaching the robot to translate** — and teaching *yourself* not to rent the reader. Babylon’s menus still said *coffee*. The street said *Yerba Matte*. Closed-stack vocabulary had to become open-stack vernacular — the same light, gradients, and BRDF memory, renamed and rebottled under terms you choose. That translation *is* [VERNACULAR](../plans/vernacular.md): speak the craft in the language of ownership. The school’s punchline is blunt: **read the machine yourself** — Slang, docs, open weights — instead of forever hiring someone to recite the pour.

So they taught the robot the *recipe* in both dialects: how light folds, how gradients flow, how a small net can remember a teacher’s BRDF the way a barista once remembered a regular’s order — then how to press that memory through a French Press of live compile, train, and export.

Then they sent the robot to work **on its own**:

1. Wake the preview. Edit. Save. See.
2. Name a teacher. Train a tiny mind in-shader. Export weights you can carry.
3. Loop feedback when the craft asks for trails and memory.
4. When the city of nodes is no longer enough, graduate the robot into a wider host — still open, still yours.
5. Give the robot a quiet helper that patches and cites, never stalls the pour.

One morning the artist streamed a cup that tasted like Babylon’s best espresso and **was not Babylon’s**. Same craft; different name on the menu: **Yerba Matte**, French-pressed, deed of title clear. The towers still stood. Nobody was robbed. The robot had simply learned to **translate** — and the brew had learned to leave the city.

That is the whole job of this school: **teach the robot so Yerba Matte can walk** — and teach you to read the pour without renting the tongue.

---

## Lessons from the heist (that isn’t one)

### 1. Learn the craft, keep the cup

Babylon’s tools are fine *examples* of high-end look. They are not the only address your work may live at. Agency means you leave able to compile and ship under terms you choose — see the [manifesto](../manifesto.md). Translate their *coffee* into your **Yerba Matte**.

**Do:** open a `.slang` file and change the light.  
**Don’t:** confuse “I can demo it here” with “I own the runtime.”

### 2. The robot starts as a live loop

Before autonomy, there is hot-reload — your French Press warming up. Book of Shaders → Playground ports → neural bridges. Save → compile → image. That loop is the robot learning to walk *and* to rename what it pours.

```powershell
python -m slang_falcon.live --lesson bos/00_hello
# later: slang_playground/sp01_simple_color · sp16_simple_image · neural/n01_function_to_network
```

### 3. Yerba Matte is teacher → weights → inference

Neural shading is the press: a teacher function, autodiff, a small MLP, exportable weights, in-shader inference. Lab 4 is the hero pour.

```powershell
python -m slang_falcon.train_brdf --steps 200 --out assets/weights/brdf_mlp.bin
python -m slang_falcon.infer --weights assets/weights/brdf_mlp.bin --out assets/output/brdf_compare.png
```

Walk the [neural trilogy](../../labs/neural_trilogy/README.md) so the robot understands *why* gradients, not only *that* they exist.

### 4. Feedback is memory, not magic

Trails, ping-pong, patch graphs — Yerba Matte that remembers the last sip. Start at the stub; grow into the [feedback plan](../plans/vsynth-feedback.md).

```powershell
python -m slang_falcon.live --lesson feedback/fb01_pingpong
```

### 5. “On its own” means pipeline + helper, not crime

Autonomy here is: curriculum → train/infer CLIs → (later) [VERNACULAR](../plans/vernacular.md) AI helper that patches buffers and cites docs without freezing the preview → (later still) Falcor as a wider stage. The robot works *for* you, on *your* stack — translating closed menus into open vernacular while it runs.

### 6. Agency is literacy, not a rented reader

The software company leaves the compiler on. The people company leaves the map lit. Neither pours your Yerba Matte for you. [VERNACULAR](../plans/vernacular.md) exists so you stop begging for interpreters and learn to **read** Slang, docs, and open weights on your own bench — French Press, deed of title clear.

**Do:** open the doc the robot already found. Change the light.  
**Don’t:** confuse “someone explained it to me once” with “I can brew it tomorrow.”

### 7. Mythic punchline (school edition)

Babylon sells atmosphere under yesterday’s nouns. You ship **source and weights** under today’s name. The funny part is how often the hardest step is not the math — it is teaching the robot that *coffee* and *Yerba Matte* were always the same craft, once you brew it yourself in a French Press — and teaching yourself that the free menu was never the bottleneck. Literacy was.

---

## Companion track (curriculum map)

Read the parable, then walk this path. Lesson ids match `labs/curriculum.json`.

| Chapter | Parable beat | Lesson ids / next step |
|---------|--------------|-------------------------|
| **I. Outside the walls** | UV, time, shape — first steam | `bos/00_hello` → `bos/05_patterns` |
| **II. Speaking the vernacular** | Playground craft in local Slang | `slang_playground/sp01_simple_color` → `sp16_simple_image` → `sp15_variadic` (pick depth; `sp02`/`sp03`/`sp08` are strong) |
| **III. Naming the teacher** | Function vs network intuition | `neural/n01_function_to_network` → `neural/n04_live_neural_param` |
| **IV. The trilogy brew** | DiffSlang → neural shading → afternoon | `diffslang/d01_differentiable_attr` → … → `neural_gfx_afternoon/ng04_tiny_mlp_fit` |
| **V. Bottle the Yerba Matte** | Train, export, compare | Lab 4 / CLI: `train_brdf` · `infer` · see `labs/04_train_brdf.md` |
| **VI. Memory in the cup** | Feedback / trails | `feedback/fb01_pingpong` · plan: [vsynth-feedback](../plans/vsynth-feedback.md) |
| **VII. Robot grows a voice** | AI helper — translator in the IDE (planned) | [VERNACULAR V2](../plans/vernacular.md) · [LLM plan](../plans/llm-slang-torch-realtime.md) — docs only today |
| **VIII. Wider stage** | 3D host later | [Falcor + SAM plan](../plans/falcor-viewport-sam.md) · Phase 2 native |

**Hubs:** [Book of Shaders](../../labs/book_of_shaders/README.md) · [Slang Playground](../../labs/slang_playground/README.md) · [Neural bridges](../../labs/neural/README.md) · [Neural trilogy](../../labs/neural_trilogy/README.md) · [Feedback](../../labs/feedback/README.md)

---

## What this companion is not

- Not literal crime, hacking, or theft instructions.
- Not a rant against commercial DCCs — they are closed *ecosystems*, useful as craft references and as a dialect to translate *from*.
- Not a hit piece on NVIDIA or Google — the parable borrows them as *software* and *people* companies that left lamps on; the satire is the crowd that still rents readers for free text.
- Not an AI chat UI. When the helper lands, it lives in VERNACULAR’s plan, not in this markdown.

Open the next lesson. Change the light. Let the Yerba Matte walk.
