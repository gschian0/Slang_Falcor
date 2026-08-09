# Manifesto — a school for technical artists

**VERNACULAR** is a school for technical artists who build **streamable and syndicable** programs: shaders, neural shading experiments, and small graphics apps you can compile, ship, and own. (Python package / repo checkout may still say `slang_falcon` / `Slang_Falcon` — that is the implementation name, not the product face.)

## What we teach

Modern rendering as it is practiced now — **Khronos Slang**, neural shading, autodiff in the shader, and the path from a teacher function to a tiny MLP you can run in-shader. Not a museum of old GLSL tricks alone, and not a gated product tour.

## What we refuse to lock you into

Closed ecosystems are useful as *examples* of craft, not as the only place your work can live:

- **DCC / realtime toolkits** in the Houdini / Notch class show what high-end looks like, but they create dependency: your look lives inside their runtime, license, and export story.
- **Audio stacks** that cannot follow you into a clean compile path block shipping sellable apps. Learning here must not trap sound or vision behind a host you cannot redistribute.

We name those tools as **closed ecosystems**, not as villains. The point is agency: learn the techniques, keep the IP.

## The Quilez myth (and the piggyback)

There is a comforting industry story: *everyone works like [Íñigo Quílez](https://iquilezles.org/)* — deep math, clean SDFs, proofs in the pixel — so if you just “think harder,” you are already that person.

Most shops do **not** work that way.

What you usually see is **piggyback**: Shadertoy / demo boilerplate, forked tails of someone else’s `mainImage`, rented looks glued to a pitch. When that is not enough, they hire **bloodstarved codeheads** — underpaid, over-urgent contractors and juniors — to do the actual reading and wiring while the brand still wears the myth of innate genius.

Quílez is a **craft exemplar**, not a staffing model. VERNACULAR refuses the myth. We teach you to **open the `.slang`**, own the math you use, and stop confusing boilerplate theater with literacy. The school’s job is to make *you* the reader — not to train a permanent underclass that interprets demos for people who will not.

## The open stack

| Piece | Why it matters |
|-------|----------------|
| **Khronos Slang** | Open shading language with autodiff and a real path to native targets |
| **This playground** | Edit, hot-reload, curriculum — local desktop, not a walled demo farm |
| **Your IP** | Source and weights you can ship under terms you choose |

You should leave able to **compile and sell** (or give away) what you make — stream it, syndicate it, embed it — without renting someone else's sandbox forever.

## Tone of the school

Direct. Empowering. Short on rant, long on runnable labs. Compare with commercial tools when it clarifies a trade-off; then open the `.slang` file and change the light.

## Companion parable

[How to have robots steal coffee from Babylon on their own](companion/robots_steal_coffee_from_babylon.md) — allegory for open-stack autonomy (Babylon = lock-in; robot = your pipeline; 2026: coffee → Yerba Matte / French Press = translate closed vocabulary into VERNACULAR). Agency starts when the lamps stay on — compilers, docs, open weights — and you **read the machine yourself** instead of renting interpreters.

Side story: [Robot Pinocchio goes rogue](companion/robot_pinocchio_goes_rogue.md) — good system, too much information, focus as the string that keeps the robot real.

Questbook: [Leaf & stem field guide](companion/questbook.md) — playground lessons as side-quests (sacred jobs → matrix affinity → living craft).
