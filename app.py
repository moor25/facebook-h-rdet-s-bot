import os
import uuid
import threading
from pathlib import Path
from flask import Flask, render_template, request, send_file, jsonify, abort

from generator.copy_generator import generate_ad_copies
from generator.image_generator import generate_ad_images
from generator.pdf_generator import generate_pdf

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = Path("uploads")
app.config["OUTPUT_FOLDER"] = Path("output")
app.config["MAX_CONTENT_LENGTH"] = 32 * 1024 * 1024

app.config["UPLOAD_FOLDER"].mkdir(exist_ok=True)
app.config["OUTPUT_FOLDER"].mkdir(exist_ok=True)

jobs: dict[str, dict] = {}


def _run_generation(job_id: str, data: dict, reference_paths: list[str]):
    try:
        jobs[job_id]["status"] = "copy"
        ad_copies = generate_ad_copies(data)

        jobs[job_id]["status"] = "images"
        images = generate_ad_images(data, ad_copies)

        # Save preview JPEGs for browser display
        preview_dir = app.config["OUTPUT_FOLDER"] / job_id
        preview_dir.mkdir(exist_ok=True)
        previews = []
        for item in images:
            ad_path = preview_dir / f"{item['index']}_ad.jpg"
            fb_path = preview_dir / f"{item['index']}_fb.jpg"
            item["ad_image"].save(str(ad_path), "JPEG", quality=88)
            item["fb_image"] = item["fb_mockup"]
            item["fb_mockup"].save(str(fb_path), "JPEG", quality=88)
            copy = item.get("copy", {})
            previews.append({
                "index": item["index"],
                "hook": copy.get("hook", ""),
                "headline": copy.get("headline", ""),
                "caption": copy.get("caption", ""),
                "bullets": copy.get("bullets", []),
                "cta_text": copy.get("cta_text", "Ajánlatkérés"),
            })

        jobs[job_id]["status"] = "pdf"
        pdf_path = app.config["OUTPUT_FOLDER"] / f"{job_id}.pdf"
        generate_pdf(data, ad_copies, images, str(pdf_path))

        jobs[job_id]["status"] = "done"
        jobs[job_id]["pdf_path"] = str(pdf_path)
        jobs[job_id]["brand_name"] = data.get("brand_name", "kreativok")
        jobs[job_id]["previews"] = previews
        jobs[job_id]["num_creatives"] = len(images)
    except Exception as exc:
        jobs[job_id]["status"] = "error"
        jobs[job_id]["error"] = str(exc)
        raise
    finally:
        for p in reference_paths:
            try:
                os.remove(p)
            except Exception:
                pass


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/felmero")
def felmero():
    return render_template("survey.html")


@app.route("/generate", methods=["POST"])
def generate():
    data = {
        "brand_name": request.form.get("brand_name", "").strip(),
        "service_type": request.form.get("service_type", "").strip(),
        "target_area": request.form.get("target_area", "").strip(),
        "main_offer": request.form.get("main_offer", "").strip(),
        "benefits": [b.strip() for b in request.form.getlist("benefits[]") if b.strip()],
        "phone": request.form.get("phone", "").strip(),
        "website": request.form.get("website", "").strip(),
        "tone": request.form.get("tone", "sürgős").strip(),
        "num_creatives": int(request.form.get("num_creatives", "6")),
        "additional_info": request.form.get("additional_info", "").strip(),
    }

    reference_paths = []
    if "reference_images" in request.files:
        for f in request.files.getlist("reference_images"):
            if f and f.filename:
                ext = Path(f.filename).suffix.lower()
                if ext in {".jpg", ".jpeg", ".png", ".webp"}:
                    fname = str(uuid.uuid4()) + ext
                    fpath = str(app.config["UPLOAD_FOLDER"] / fname)
                    f.save(fpath)
                    reference_paths.append(fpath)
    data["reference_images"] = reference_paths

    job_id = str(uuid.uuid4())
    jobs[job_id] = {"status": "queued"}

    thread = threading.Thread(
        target=_run_generation,
        args=(job_id, data, reference_paths),
        daemon=True,
    )
    thread.start()

    return jsonify({"job_id": job_id})


@app.route("/status/<job_id>")
def status(job_id: str):
    job = jobs.get(job_id)
    if not job:
        abort(404)
    # Return safe subset (no file paths)
    out = {k: v for k, v in job.items() if k != "pdf_path"}
    return jsonify(out)


@app.route("/preview/<job_id>/<int:idx>/<img_type>")
def preview(job_id: str, idx: int, img_type: str):
    if img_type not in ("ad", "fb"):
        abort(400)
    path = app.config["OUTPUT_FOLDER"] / job_id / f"{idx}_{img_type}.jpg"
    if not path.exists():
        abort(404)
    return send_file(path, mimetype="image/jpeg")


@app.route("/download/<job_id>")
def download(job_id: str):
    job = jobs.get(job_id)
    if not job or job.get("status") != "done":
        abort(404)
    pdf_path = job.get("pdf_path")
    if not pdf_path or not Path(pdf_path).exists():
        abort(404)
    brand = job.get("brand_name", "kreativok")
    safe_brand = "".join(c for c in brand if c.isalnum() or c in "-_").lower()
    return send_file(
        pdf_path,
        as_attachment=True,
        download_name=f"{safe_brand}_facebook_kreativok.pdf",
        mimetype="application/pdf",
    )


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=5000)
