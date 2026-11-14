import json,glob,re,random,csv,collections,os,hashlib
D='/home/claude/dataset/data'
SYS="أنت مساعد جامعة العلوم والتكنولوجيا الأردنية لشؤون الأنظمة والتعليمات. أجب بالعربية فقط اعتماداً على الوثائق الرسمية للجامعة، واختم كل جواب بذكر المصدر (اسم الوثيقة ورقم المادة). إذا لم تجد الجواب في الوثائق فقل: «لا أعرف» ووجّه الطالب للجهة المسؤولة."
def norm(s):
    s=re.sub(r'[ً-ْٰـ]','',s)
    s=s.translate(str.maketrans('أإآٱىةؤئ٠١٢٣٤٥٦٧٨٩','اااايهوي0123456789'))
    s=re.sub(r'[^\w\s]',' ',s); return re.sub(r'\s+',' ',s).strip()
def toks(s): return [t for t in norm(s).split() if len(t)>1]
C=[json.loads(l) for l in open(f'{D}/clean/chunks.jsonl')]
bydoc=collections.defaultdict(list)
for c in C: bydoc[c['doc_id']].append(c)
ctok={c['chunk_id']:collections.Counter(toks(c['text_normalized'])) for c in C}
W={d['doc_id']:d for d in json.load(open('/home/claude/dataset/worklist.json'))}
facts=[]
for f in sorted(glob.glob(f'{D}/sft/raw/*.jsonl')):
    for l in open(f):
        o=json.loads(l); o['source_group']='regulation'
        o['audience']='graduate' if W.get(o['doc_id'],{}).get('aud')=='graduate' else 'bachelor'
        facts.append(o)
report={'link':collections.Counter()}
# 1 link chunks
for o in facts:
    body=o['answer'].split(' المصدر:')[0]; at=set(toks(body)); m=re.search(r'المادة\s*\(?(\d+)',o['cite'])
    art=int(m.group(1)) if m else None
    best=[]
    for c in bydoc.get(o['doc_id'],[]):
        ov=sum(1 for t in at if t in ctok[c['chunk_id']])/max(1,len(at))
        bonus=0.25 if (art is not None and c.get('article')==art) else 0
        best.append((ov+bonus,ov,c['chunk_id']))
    best.sort(reverse=True)
    if not best: o['chunk_ids']=[]; o['link_score']=0; report['link']['no_chunks']+=1; continue
    ids=[best[0][2]]
    if len(best)>1 and best[1][0]>=best[0][0]-0.08 and best[1][1]>0.3: ids.append(best[1][2])
    o['chunk_ids']=ids; o['link_score']=round(best[0][1],2)
    report['link']['high' if best[0][1]>=0.5 else 'mid' if best[0][1]>=0.3 else 'low']+=1
plans=[json.loads(l)|{'source_group':'plan'} for l in open(f'{D}/sft/raw_plans.jsonl')]
refs=[json.loads(l)|{'source_group':'refusal'} for l in open(f'{D}/sft/raw_refusals.jsonl')]
allf=facts+plans+refs
OVR={("0214-b002","jo"):"إذا غبت كثير عن المحاضرات، ايمتى بنحرم وشو بنحطلي؟",
("0214-c005","jo"):"آخر موعد للانسحاب من المساق ايمتى بكون؟",
("0214-c030","jo"):"عشان أتخرج بكالوريوس، كم لازم يكون تراكمي على الأقل؟",
("0282-a011","jo"):"طالب الدكتوراه كم ساعة بنزل بالفصل العادي؟",
("0268-a001","jo"):"شو أهداف كلية الدراسات العليا حسب تعليماتها؟",
("0275-a004","jo"):"بالماجستير، كم نسبة الي بنقبلوا ومعدلهم مقبول؟"}
for o in allf:
    for st in list(o['questions']):
        if (o['fact_id'],st) in OVR: o['questions'][st]=OVR[(o['fact_id'],st)]
# 2 numbers check (text-verified reg facts vs clean2 text)
numbad=[]
for o in facts:
    if o.get('verified_from')!='text': continue
    p=f"/home/claude/work/clean2/{o['doc_id']}.txt"
    if not os.path.exists(p): continue
    def nums(x):
        x=x.translate(str.maketrans('٠١٢٣٤٥٦٧٨٩','0123456789')).replace(',','.').replace('٫','.')
        return set(re.findall(r'\d+(?:\.\d+)?',x))
    TN=nums(open(p).read()); TN|={n.split('.')[0] for n in TN}|{n.rstrip('0').rstrip('.') for n in TN if '.' in n}
    for n in nums(o['answer'].split(' المصدر:')[0]):
        if n not in TN and n.rstrip('0').rstrip('.') not in TN and not any(n==t[::-1] for t in TN):
            numbad.append((o['fact_id'],n))
# 3 test leakage + dedup
test=list(csv.DictReader(open('/home/claude/repos/frieh7_just-regulations-assistant/eval/seed_test_set.csv',encoding='utf-8-sig')))
def grams(s,n=4):
    t=norm(s).split(); return {' '.join(t[i:i+n]) for i in range(max(1,len(t)-n+1))}
tq=[(r['id'],norm(r['question']),grams(r['question'])) for r in test]
leaks=[]; seen={}; dups=[]
for o in allf:
    for st,q in o['questions'].items():
        nq=norm(q); g=grams(q)
        for tid,tn,tg in tq:
            j=len(g&tg)/max(1,len(g|tg))
            if nq==tn or j>=0.5: leaks.append((o['fact_id'],st,tid,round(j,2),q))
        if nq in seen and seen[nq]!=o['fact_id']: dups.append((o['fact_id'],st,seen[nq],q))
        seen.setdefault(nq,o['fact_id'])
json.dump({'link':report['link'],'numbers_not_in_text':numbad,'test_leaks':leaks,'dup_questions':dups,
  'counts':{g:sum(1 for o in allf if o['source_group']==g) for g in('regulation','plan','refusal')}},
  open(f'{D}/sft/checks_report.json','w'),ensure_ascii=False,indent=1)
print(report['link'],'numbad',len(numbad),'leaks',len(leaks),'dups',len(dups))
if os.environ.get('WRITE')!='1': raise SystemExit
drop={(a,b) for a,b,*_ in leaks}|{(a,b) for a,b,*_ in dups}
# 4 split by fact_id (stratified by group), 90/10
random.seed(42); split={}
for g in('regulation','plan','refusal'):
    ids=sorted(o['fact_id'] for o in allf if o['source_group']==g); random.shuffle(ids)
    k=max(1,round(len(ids)*0.1))
    for i,x in enumerate(ids): split[x]='val' if i<k else 'train'
with open(f'{D}/sft/facts.jsonl','w',encoding='utf-8') as fh:
    for o in allf: o['split']=split[o['fact_id']]; fh.write(json.dumps(o,ensure_ascii=False)+'\n')
cnt=collections.Counter()
fh={s:open(f'{D}/sft/{s}.jsonl','w',encoding='utf-8') for s in('train','val')}
for o in allf:
    for st,q in o['questions'].items():
        if (o['fact_id'],st) in drop: continue
        r={"id":f"{o['fact_id']}-{st}","fact_id":o['fact_id'],"doc_id":o['doc_id'],"chunk_ids":o['chunk_ids'],"type":o['type'],
           "source_group":o['source_group'],"audience":o['audience'],"style":"jo" if st=='jo' else "msa",
           "verified_from":o.get('verified_from'),
           "messages":[{"role":"system","content":SYS},{"role":"user","content":q},{"role":"assistant","content":o['answer']}]}
        fh[o['split']].write(json.dumps(r,ensure_ascii=False)+'\n'); cnt[(o['split'],o['source_group'])]+=1
for x in fh.values(): x.close()
print(dict(cnt))
# 5 CPT: split by document
random.seed(7); docs=sorted(bydoc); random.shuffle(docs)
k=round(len(docs)*0.1); held=set(docs[:k])
pl=[json.loads(l) for l in open('/home/claude/dataset/pretrain.jsonl')]
pidx=list(range(len(pl))); random.shuffle(pidx); pheld=set(pidx[:round(len(pl)*0.1)])
ft=open(f'{D}/cpt/train.jsonl','w',encoding='utf-8'); fhd=open(f'{D}/cpt/heldout.jsonl','w',encoding='utf-8'); cc=collections.Counter()
for d in sorted(bydoc):
    txt="\n".join(c['text_normalized'] for c in bydoc[d]); c0=bydoc[d][0]
    r={"doc_id":d,"title":c0['doc_title'],"category":c0['category'],"audience":c0['audience'],"quality":c0['quality'],"text":c0['doc_title']+"\n"+txt}
    (fhd if d in held else ft).write(json.dumps(r,ensure_ascii=False)+'\n'); cc['held' if d in held else 'train']+=1; cc['w_'+('held' if d in held else 'train')]+=len(txt.split())
for i,p in enumerate(pl):
    r={"doc_id":f"plan-doc-{i:03d}","title":p['text'].split('\n')[0][:80],"category":"study_plans","audience":"student","quality":"structured","text":p['text']}
    (fhd if i in pheld else ft).write(json.dumps(r,ensure_ascii=False)+'\n'); cc['held' if i in pheld else 'train']+=1; cc['w_'+('held' if i in pheld else 'train')]+=len(p['text'].split())
print(dict(cc))
json.dump({'sft_pairs':{f"{a}/{b}":n for (a,b),n in cnt.items()},'cpt':dict(cc),'cpt_heldout_docs':sorted(held)},open(f'{D}/build_stats.json','w'),ensure_ascii=False,indent=1)
