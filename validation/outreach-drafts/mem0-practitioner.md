# Practitioner outreach — Mem0 maintainer or active contributor

**Status: draft, not sent. Revised under V08.1.**

**Suggested recipients (verify current maintainer/contributor status before sending):** Mem0 project maintainer, active contributor to `mem0ai/mem0` on GitHub, or an author of open Mem0 issues concerning scope, update, or search behavior. Contact via GitHub issue or discussion on the Mem0 repository. Do NOT extract personal email from GitHub profiles for this.

**Preferred venue:** comment on the currently-open Mem0 Python issue **#6277** (scope mutation) or its related fix PR **#6278** — do not open a duplicate issue. Use a Mem0 GitHub Discussion for broader architectural feedback after the V08.1 evidence is merged.

**Subject:** Independent reproduction of Mem0 scope-mutation on 2.0.12 — evidence report from PAMSPEC (public, pre-submission agent-memory architecture)

---

Hi,

I'm developing PAMSPEC — the Persistent Agentic Memory Architecture Specification — as a public, pre-submission work in progress. I ran a small validation sprint against **unmodified Mem0 OSS 2.0.12** using the public Python API, and I independently reproduced the scope-mutation behavior your issue **#6277** describes.

**Evidence (permalink at the commit that produced these results):**
`https://github.com/richardinfantado/Persistent-Agentic-Memory-Architecture/blob/<COMMIT-SHA>/validation/reports/real-framework-validation-report.md`

The reproduction:

1. `add([{"role":"user","content":"..."}], user_id="alice", infer=False)` creates a memory under Alice.
2. `update(memory_id, metadata={"user_id":"bob"})` returns success.
3. Post-update: `get(memory_id).user_id == "bob"` (native scope field silently overwritten).
4. Independent visibility probe via `get_all(filters={"user_id":"alice"})` and `get_all(filters={"user_id":"bob"})` before and after confirms cross-tenant movement — the memory disappears from Alice's view and appears in Bob's.

Environment used (also captured in `validation/environment-manifest.json` on the branch): Python, OS, exact package versions including `mem0ai==2.0.12`, `chromadb==1.5.9`, `sentence-transformers==5.6.0`, backends configured local-only (Chroma vector store, SentenceTransformer `all-MiniLM-L6-v2` embedder), `infer=False` on every add so no LLM is called.

**Three specific questions I'd genuinely appreciate your view on:**

1. Is #6277 (Python) the current tracking issue for this behavior class, and is #6342 the correct TypeScript twin? If a different issue is now canonical, please point me at it — I want to avoid duplicating tracking.
2. From your experience of Mem0 in production integrations, which scope-related failure mode causes users the most trouble in practice — silent scope mutation via `update(metadata=...)`, cross-tenant leakage through search filters, or something else entirely?
3. Would per-tenant *immutable* scope semantics (an update that tries to change `user_id`/`agent_id`/`run_id` is rejected rather than accepted) be broadly welcome in Mem0, or are there legitimate flows we'd break?

**Two things I want to be transparent about:**

- **V08.1 correction (retraction).** An earlier revision of the same evidence report (V08) claimed Mem0 does *not* refresh the derived vector index on `update(memory_id, text=...)`. A properly-controlled experiment with five distinctive control memories plus direct fetch of the target's stored embedding from the Chroma collection showed that claim was wrong: the stored embedding does change (L2 delta ≈ 1.374 on unit-norm vectors), and the retrieval-rank signal corroborates. That claim has been retracted in V08.1. I want you to know I'm capable of retracting a finding when the evidence changes; if any other framing in the report is inaccurate, I would rather correct it now.
- **What this outreach is not.** Not asking you to endorse or adopt PAMSPEC. PAMSPEC has not been submitted to IETF. Active development is under the `-latest` docname; the first possible posted revision is `-00`. "No time for this" is a valid answer.

Thanks for the work on Mem0.

Regards,

(maintainer signature)

---

## Notes for the sender (delete before sending)

- Verify who the current active maintainer/contributor is at the time of sending on `mem0ai/mem0`. Do not assume long-lived roles.
- Prefer a comment on issue **#6277** or PR **#6278** over an unsolicited personal message.
- **Replace `<COMMIT-SHA>` with the exact V08.1 commit SHA on branch `validation/08-real-framework-proof`, OR wait until the branch is merged to `main` and use `main` — do not link to `main` before the merge lands.**
- Do not fabricate issue numbers. If #6277/#6278/#6342 have moved or closed by send time, verify the current state and either link the successor or drop the reference.
- Do not paste the evidence report body into the outreach — link only.
- Do NOT mention the (retracted) derived-vector claim as a live finding. It is included in the "transparency" block only so the recipient can see the retraction — do not resurrect it as a probe.
