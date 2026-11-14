import json,random,re
random.seed(20261113)
P=json.load(open('/home/claude/dataset/all_plans.json'))
out=open('/home/claude/dataset/data/sft/raw_plans.jsonl','w',encoding='utf-8')
def cl(s): return re.sub(r'\s+',' ',s).strip()
PT={'سابق دراسة':'دراسة','سابق نجاح':'النجاح في','متزامن':'التسجيل بالتزامن مع','سابق أو متزامن':'دراسة (سابقاً أو بالتزامن)','سابق نجاح أو متزامن':'النجاح في (أو التسجيل بالتزامن مع)'}
n=0
def emit(pl,k,typ,ans,q1,q2,qj,extra=None):
    global n
    src=f"الخطة الدراسية لتخصص {pl['major']}، رقم الخطة {pl['plan_no']}"
    d={"fact_id":f"P{pl['plan_no']}-{k:02d}","doc_id":f"plan-{pl['plan_no']}","chunk_ids":[f"plan-{pl['plan_no']}"],"type":typ,
       "cite":f"رقم الخطة {pl['plan_no']}","verified_from":"structured","answer":cl(ans)+f" المصدر: {src}.",
       "questions":{"msa_1":cl(q1),"msa_2":cl(q2),"jo":cl(qj)},"audience":"bachelor","major":pl['major'],"faculty":pl['faculty']}
    if extra: d.update(extra)
    out.write(json.dumps(d,ensure_ascii=False)+"\n"); n+=1
def pick(lst,i): return lst[i%len(lst)]
for pi,pl in enumerate(P):
    m=pl['major']; f=pl['faculty']; h=pl['total_hours']; y=pl['year']; k=0
    # 1 hours
    k+=1; emit(pl,k,"plan_hours",f"عدد الساعات المعتمدة المطلوبة للتخرج في تخصص {m} ({pl['degree']}) هو {h} ساعة معتمدة حسب خطة عام {y}.",
      pick([f"كم عدد الساعات المعتمدة في خطة تخصص {m}؟",f"ما مجموع الساعات المعتمدة المطلوبة للتخرج من تخصص {m}؟",f"كم ساعة معتمدة يتطلب الحصول على بكالوريوس {m}؟"],pi),
      pick([f"ما عدد ساعات الخطة الدراسية لبكالوريوس {m}؟",f"كم ساعة معتمدة يدرس طالب {m} حتى يتخرج؟",f"ما إجمالي ساعات خطة {m} في جامعة العلوم والتكنولوجيا؟"],pi+1),
      pick([f"كم ساعة تخصص {m}؟",f"كم ساعة لازم أخلص عشان أتخرج من {m}؟",f"خطة {m} كم ساعة؟"],pi))
    # 2 faculty
    k+=1; emit(pl,k,"major_faculty",f"تخصص {m} يتبع {f} في جامعة العلوم والتكنولوجيا الأردنية.",
      pick([f"إلى أي كلية يتبع تخصص {m}؟",f"ما الكلية التي تطرح تخصص {m}؟"],pi),
      pick([f"في أي كلية يدرس تخصص {m}؟",f"تخصص {m} تابع لأي كلية؟"],pi),
      pick([f"تخصص {m} بأي كلية؟",f"{m} تبع أي كلية؟",f"وين بلاقي تخصص {m}، بأي كلية؟"],pi))
    # 3 categories
    cats=[c for c in pl['categories'] if c.get('required_hours')]
    if cats:
        parts="، ".join(f"{c['category']} ({c['required_hours']} ساعة)" for c in cats)
        k+=1; emit(pl,k,"plan_structure",f"تتوزع ساعات خطة تخصص {m} البالغة {h} ساعة معتمدة كما يلي: {parts}.",
          f"كيف تتوزع الساعات المعتمدة في خطة تخصص {m}؟",
          pick([f"كم ساعة متطلبات الجامعة والكلية والقسم في خطة {m}؟",f"ما مكونات الخطة الدراسية لتخصص {m}؟"],pi),
          pick([f"كيف مقسمة ساعات خطة {m}؟",f"كم ساعة متطلبات جامعة وكم كلية بخطة {m}؟"],pi))
    spec=[(c['category'],x) for c in pl['categories'] if c['category'] in('قسم إجباري','تخصص إجباري','كلية إجباري') for x in c['courses']]
    seen=set(); spec=[t for t in spec if not (t[1]['name'] in seen or seen.add(t[1]['name']))]
    wp=[t for t in spec if t[1]['prerequisites']]; np_=[t for t in spec if not t[1]['prerequisites']]
    random.shuffle(wp); random.shuffle(np_)
    for i,(cat,x) in enumerate(wp[:3]):
        nm=cl(x['name']); code=x['code']
        pr=" و".join(f"{PT[q['type']]} {cl(q['name'])} ({q['code']})" for q in x['prerequisites'])
        k+=1; emit(pl,k,"prereq",f"في تخصص {m}، المتطلب السابق لمادة {nm} ({code}) هو {pr}.",
          pick([f"ما المتطلب السابق لمادة {nm} في تخصص {m}؟",f"ما المساق الذي يجب دراسته قبل {nm} في خطة {m}؟"],i),
          pick([f"هل لمادة {nm} متطلب سابق في خطة {m}؟ وما هو؟",f"ماذا يشترط لتسجيل مادة {nm} في تخصص {m}؟"],i+pi),
          pick([f"شو متطلب مادة {nm} بتخصص {m}؟",f"شو لازم أكون ماخد قبل {nm}؟ (تخصص {m})",f"بقدر أنزل {nm} بدون ما آخد اشي قبلها؟ (تخصص {m})"],i+pi),{"course_code":code})
    for i,(cat,x) in enumerate(np_[:1]):
        nm=cl(x['name']); code=x['code']
        k+=1; emit(pl,k,"prereq_none",f"في تخصص {m}، مادة {nm} ({code}) ليس لها متطلب سابق في الخطة الدراسية.",
          f"هل لمادة {nm} متطلب سابق في تخصص {m}؟",f"ما المتطلب السابق لمادة {nm} في خطة {m}؟",
          pick([f"مادة {nm} إلها متطلب بتخصص {m}؟",f"بقدر أسجل {nm} مباشرة بدون متطلب؟ (تخصص {m})"],pi),{"course_code":code})
    rest=[t for t in wp[3:]+np_[1:]]
    for i,(cat,x) in enumerate(rest[:1]):
        nm=cl(x['name']); code=x['code']
        k+=1; emit(pl,k,"course_info",f"مادة {nm} ({code}) في تخصص {m} عدد ساعاتها المعتمدة {x['credit_hours']}، وهي من متطلبات {cat}، ونمط تدريسها {x['delivery']}.",
          f"كم عدد الساعات المعتمدة لمادة {nm} في تخصص {m}؟",
          pick([f"هل مادة {nm} إجبارية في خطة {m}؟ وما نمط تدريسها؟",f"ما نوع مادة {nm} في خطة {m} وكيف تدرّس؟"],pi),
          pick([f"مادة {nm} كم ساعة بتخصص {m}؟",f"مادة {nm} وجاهي ولا أونلاين؟ (تخصص {m})"],pi),{"course_code":code})
print(n)
