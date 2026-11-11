import base64, json, os, re
from typing import List
from anthropic import Anthropic
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="KWA Notebook Scanner API", version="1.0.0")
cors = os.getenv("CORS_ORIGINS", "*")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if cors == "*" else [x.strip() for x in cors.split(",") if x.strip()],
    allow_credentials=False, allow_methods=["GET", "POST", "OPTIONS"], allow_headers=["*"]
)

PROMPT = r"""
Read these handwritten Kerala Water Authority water-quality notebook page photos.
Pages may be sideways. A left/right spread continues the same sample rows; merge
the two pages by sample number. Ignore bracketed sample types such as (FP), (SPl),
(V+NH3). Skip QC rows and rows without sample numbers.

Left columns: sample no, pH, EC, TDS, Turb, Ac (acidity titre), Alk (alkalinity titre),
TH (hardness titre), Ca (calcium titre), sometimes Cl (chloride titre).
Right columns: Cl if absent on left, SO4, Fe, NO3, F and C/O in either order
(F is a small decimal; C/O is colour/odour such as 40/Disag or 1/A;
A=Agreeable, D/Disag=Disagreeable), R.C (residual chlorine), NH3.

Use the corrected final value for overwritten/struck-through values.
Copy values as strings. Use "-" for dash/untested and "nil" for Nil.
Use "" only if unreadable. col is colour number only; od is Agreeable,
Disagreeable or Muddy odour. Put uncertain field keys in unsure.
If a date is written dd/mm/yy, return YYYY-MM-DD, otherwise null.
Do not guess unreadable digits. Return ONLY valid JSON, no Markdown.

Schema:
{"date":null,"rows":[{"s":"","ph":"","ec":"","tds":"","tu":"","ac":"","alk":"",
"th":"","ca":"","cl":"","so4":"","fe":"","no3":"","f":"","col":"","od":"",
"nh3":"","rc":"","unsure":[]}]}
"""
ALLOWED = {"image/jpeg", "image/png", "image/webp", "image/gif"}

@app.get("/")
def root():
    return {"status":"ok","service":"KWA Notebook Scanner API"}

@app.get("/health")
def health():
    return {"status":"healthy"}

@app.post("/api/scan")
async def scan_notebook(files: List[UploadFile] = File(...)):
    key = os.getenv("ANTHROPIC_API_KEY")
    if not key:
        raise HTTPException(503, "Backend missing ANTHROPIC_API_KEY. Add it in Render Environment.")
    if not files or len(files) > 4:
        raise HTTPException(400, "Upload between 1 and 4 notebook photos.")
    blocks = []
    for idx, f in enumerate(files, 1):
        mime = (f.content_type or "").lower()
        if mime not in ALLOWED:
            raise HTTPException(415, f"Photo {idx}: use JPEG, PNG, WebP or GIF.")
        raw = await f.read()
        if not raw:
            raise HTTPException(400, f"Photo {idx} is empty.")
        if len(raw) > 7 * 1024 * 1024:
            raise HTTPException(413, f"Photo {idx} exceeds 7 MB.")
        blocks.append({"type":"image","source":{
            "type":"base64","media_type":mime,"data":base64.b64encode(raw).decode("ascii")
        }})
    blocks.append({"type":"text","text":PROMPT})
    try:
        client = Anthropic(api_key=key)
        msg = client.messages.create(
            model=os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6"),
            max_tokens=8000, temperature=0,
            messages=[{"role":"user","content":blocks}]
        )
        raw_text = "\n".join(b.text for b in msg.content if getattr(b,"type",None)=="text").strip()
        raw_text = re.sub(r"^```(?:json)?\s*", "", raw_text)
        raw_text = re.sub(r"\s*```$", "", raw_text)
        result = json.loads(raw_text)
        if not isinstance(result,dict) or not isinstance(result.get("rows"),list):
            raise ValueError("Unexpected JSON structure")
        result.setdefault("date",None)
        return result
    except json.JSONDecodeError:
        raise HTTPException(502, "Claude returned invalid JSON. Try clearer photos.")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(502, f"Claude scan failed ({type(exc).__name__}). Check Render logs.")
