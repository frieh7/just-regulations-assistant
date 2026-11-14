import json,sys,re
def save(doc_id,doc_name,facts,batch,verified="text"):
    """facts: list of (type, chunk_ids, cite, answer, q_msa1, q_msa2, q_jo)"""
    out=[]
    for n,f in enumerate(facts,1):
        t,ch,cite,ans,q1,q2,q3=f
        src=f"المصدر: {doc_name}، {cite}."
        out.append({"fact_id":f"{doc_id}-{batch}{n:03d}","doc_id":doc_id,"chunk_ids":[f"{doc_id}-{c:03d}" for c in ch],
                    "type":t,"cite":cite,"verified_from":verified,"answer":ans.rstrip()+" "+src,"questions":{"msa_1":q1,"msa_2":q2,"jo":q3}})
    p=f"/home/claude/dataset/data/sft/raw/{doc_id}_{batch}.jsonl"
    with open(p,'w',encoding='utf8') as fh:
        for o in out: fh.write(json.dumps(o,ensure_ascii=False)+'\n')
    print(p,len(out))
