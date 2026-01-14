from __future__ import annotations
import json, os, random, uuid
from app.db import connect, init_db
from app.providers.embedding import EmbeddingProvider

CATEGORIES = ["sofa","coffee_table","side_table","dining_table","chair","floor_lamp","table_lamp","pendant_light"]
BRANDS = ["Wayfair","West Elm","CB2","Pottery Barn","Article","Boutique"]

def main():
    init_db()
    con = connect()
    cur = con.cursor()
    cur.execute("DELETE FROM products")
    con.commit()

    emb = EmbeddingProvider()
    rnd = random.Random(1337)

    for cat in CATEGORIES:
        for i in range(12):  # 96 products + extras below
            price = round(rnd.uniform(80, 1800), 2)
            brand = rnd.choice(BRANDS)
            name = f"{cat.replace('_',' ').title()} {i+1}"
            # deterministic embedding from (cat,name)
            blob = (cat + "|" + name).encode("utf-8")
            vec = emb.embed(blob)
            pid = str(uuid.uuid4())
            aff = f"https://example.com/buy?pid={pid}&aff=demo"
            cur.execute(
                "INSERT INTO products(id,external_id,source,name,brand,category,price,affiliate_url,product_url,image_url,embedding_json) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                (pid, pid, "seed", name, brand, cat, price, aff, aff, None, json.dumps(vec))
            )

    con.commit()
    con.close()
    print("Seeded products.")

if __name__ == "__main__":
    main()
