import json,re,glob,collections,sys
def norm(t):
    t=re.sub(r'[ً-ْـ]','',t); t=t.translate(str.maketrans('٠١٢٣٤٥٦٧٨٩','0123456789'))
    t=re.sub('[أإآ]','ا',t); t=t.replace('ى','ي').replace('ة','ه')
    return re.findall(r'[ء-يa-zA-Z0-9]+',t)
def grams(w,n=3): return {tuple(w[i:i+n]) for i in range(len(w)-n+1)}
chunks=[json.loads(l) for l in open('clean/chunks.jsonl')]
ans=collections.defaultdict(set)
for f in glob.glob('sft/raw/*.jsonl'):
    for l in open(f):
        d=json.loads(l); ans[d['doc_id']]|=grams(norm(d['answer']))
for f in ['sft/raw_plans.jsonl','sft/raw_refusals.jsonl']: pass
EXCL={'0165','0284','0254'}
res=collections.defaultdict(lambda:[0,0,0,0])
for c in chunks:
    if c['audience'] not in ('student','graduate','students','both','all') and not str(c['audience']).startswith(('stud','grad')): continue
    if c['doc_id'] in EXCL: continue
    g=grams(norm(c['text_normalized'] if c.get('text_normalized') else c['text']))
    r=len(g&ans[c['doc_id']])/max(1,len(g))
    s=res[c['doc_id']]; s[0]+=1; s[3]+=c['n_words']
    if r<0.12: s[1]+=1; s[2]+=c['n_words']
json.dump(res,open('/tmp/cov.json','w'))
rows=sorted(((v[2],k,v) for k,v in res.items() if v[1]),reverse=True)
print(len(res),'docs',sum(v[0] for v in res.values()),'chunks; gap chunks',sum(v[1] for v in res.values()),'words',sum(v[2] for v in res.values()),'/',sum(v[3] for v in res.values()))
print('docs with gaps',len(rows))
for w,k,v in rows[:40]: print(k,v[1],'/',v[0],w)
