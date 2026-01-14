from matching_core.ranking import Product, cosine_similarity, rank_products, pick_budget_alternatives

def test_cosine_similarity_identity():
    assert cosine_similarity([1.0, 0.0], [1.0, 0.0]) == 1.0

def test_rank_products_orders_by_similarity():
    q = [1.0, 0.0]
    p1 = Product("1","A","B","sofa",100,"#", [1.0, 0.0])
    p2 = Product("2","C","D","sofa",90,"#", [0.0, 1.0])
    ranked = rank_products(q, [p2, p1], top_k=2)
    assert ranked[0][0].id == "1"

def test_budget_alternatives_cheaper_than_top():
    q = [1.0, 0.0]
    top = Product("top","Top","Brand","sofa",200,"#", [1.0, 0.0])
    cheap = Product("c","Cheap","Brand","sofa",100,"#", [1.0, 0.0])
    ranked = [(top, 1.0),(cheap, 0.9)]
    alts = pick_budget_alternatives(ranked, top=top, k=1)
    assert alts[0].id == "c"
