"""리소스팩 빌더 — 파일을 모아 폴더/zip 으로 쓴다"""
import io
import json
import os
import shutil
import zipfile

from PIL import Image

PACK_FORMAT = 75          # 1.21.11 (기존 olympus_pack 과 동일)


class Pack:
    def __init__(self, ns="bg"):
        self.ns = ns
        self.files = {}            # 경로 → bytes

    def put(self, path, data):
        if isinstance(data, (dict, list)):
            data = json.dumps(data, ensure_ascii=False, indent=1).encode("utf-8")
        elif isinstance(data, str):
            data = data.encode("utf-8")
        self.files[path] = data

    def png(self, path, img):
        buf = io.BytesIO()
        img.save(buf, "PNG", optimize=True)
        self.files[path] = buf.getvalue()

    # ── 아이템 모델 (1.21.4+ items/ 정의 + models/)
    def item_model(self, name, model_json):
        """name = 'deco/zeus_bolt' → bg:deco/zeus_bolt 로 item_model 컴포넌트에서 사용"""
        self.put(f"assets/{self.ns}/models/item/{name}.json", model_json)
        self.put(f"assets/{self.ns}/items/{name}.json", {"model": {"type": "minecraft:model", "model": f"{self.ns}:item/{name}"}})

    def texture(self, name, img):
        """textures/item/<name>.png → 참조 'bg:item/<name>'"""
        self.png(f"assets/{self.ns}/textures/item/{name}.png", img)
        return f"{self.ns}:item/{name}"

    def write(self, folder, zpath, description):
        self.put("pack.mcmeta", {"pack": {"description": description, "pack_format": PACK_FORMAT,
                                          "min_format": PACK_FORMAT, "max_format": PACK_FORMAT}})
        if os.path.exists(folder):
            shutil.rmtree(folder)
        for p, d in self.files.items():
            fp = os.path.join(folder, p)
            os.makedirs(os.path.dirname(fp), exist_ok=True)
            with open(fp, "wb") as f:
                f.write(d)
        os.makedirs(os.path.dirname(zpath), exist_ok=True)
        with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
            for p in sorted(self.files):
                zi = zipfile.ZipInfo(p, (2026, 1, 1, 0, 0, 0))
                zi.compress_type = zipfile.ZIP_DEFLATED
                z.writestr(zi, self.files[p])
        return len(self.files)
