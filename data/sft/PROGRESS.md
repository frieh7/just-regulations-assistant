# SFT generation progress (raw facts, 3 phrasings each; expand to pairs later)
- 0214 تعليمات منح درجة البكالوريوس (1987 المعدلة): DONE (batches a,b,c) — chunks 1-46
- 0183 الأعذار الطبية: DONE (a)
- 0229 انعقاد الامتحانات: DONE (a, image-verified; pages 4-5 are student pledge forms, skipped—see 0230)
## Extraction caveats
- text-layer garbled / zero->one bug / OCR digits: facts for these docs are written from page IMAGES (verified_from=image). List in worklist.json flags.
- 0232 أسس بناء برامج الامتحانات: DONE (a, image)
- 0182 التسهيلات للإعاقة: DONE (a, text)
## Reliability rule (final): worklist.json 'mode' = text (digits ok) or image (digits garbled/unreliable; read page images). 34 text-mode docs, 94 image-mode docs (198 pages).
- 0181 التأمين الطبي: DONE (a, image); 0193 الصالة الرياضية: DONE (a, image)
- 0195 دعم المؤتمرات (image), 0243 امتحان الإكمال/بيطري (image), 0201 طرح الجدول (image), 0172 منع التدخين, 0194 تعليق الدراسة (text): DONE
- 0171 تعليمات تأديب الطلبة 2024: DONE (a, image)
- 0170 نظام تأديب الطلبة 1999: DONE (a, image)
- DONE: 0175,0174,0173,0166,0167,0168,0176,0177,0178,0179,0169 (batch a)
- DONE: 0196-0200,0202-0212 (fees batch)
DONE: 0180,0185-0192,0184 (student activities, ~70 facts)
DONE: 0213,0215,0220,0222,0223,0240,0242
DONE: 0250-0253,0255-0265 (parallel/bridging)
DONE: 0266-0270, 0275 (a,b,c)
DONE: 0271,0273
DONE: 0272,0274,0276,0285,0287,0289
DONE: 0277,0280,0283,0288
DONE: 0278,0279
DONE: 0281,0282,0286(صفحات 1-4 فقط؛ الباقي قرارات رسوم قديمة 2009-2012 — CPT فقط، تحتاج تأكيد حداثة قبل SFT)
SKIP-SFT: 0284 (أسس استحداث برامج — مؤسسي لا يخص الطالب، CPT فقط)
DONE: 0248,0238,0161,0128,0164
SKIP-SFT: 0165 (نادي الموظفين — لا يخص الطالب)، 0254 (جدول X — يحتاج صورة؛ مؤجل)
FINAL BUILD: 1548 facts / 4179 train / 465 val ; CPT 392/44 ; zip in outputs

== حالة 2026-11-13 10:40 (إيقاف مؤقت بطلب المستخدم) ==
- البيانات النهائية الحالية: 1548 حقيقة / 4179 train / 465 val ; CPT 392/44. الملفات سليمة.
- المطلوب من المستخدم: تغطية كاملة لوثائق الطلبة والدراسات العليا، لا بند ناقص.
- فحص الفجوات: 482 مقطع من 999 بلا حقائق (46,770 كلمة من 137,868). أكبرها: 0218 (46/51 مقطع)، 0216 (34/55)، 0286، 0238، 0184، 0273، 0212، 0274، 0272، 0275، 0244، 0277.
- ملاحظة: الربط حقيقة→مقطع آلي (أفضل مقطع فقط) فالرقم تقريبي.
- الخطوة التالية: 0218 كاملة، ثم باقي الفجوات بالترتيب، إعادة الفحص بعد كل وثيقة، ثم زيادة الخطط من أسئلة حمزة بنسبة أقل من التعليمات (ملف ثابت بدون سحب أثناء التدريب).
- لا تعديل على البيانات قبل قول المستخدم «اعمل».
- مستثنى من الأسئلة (CPT فقط): 0165 نادي الموظفين، 0284 استحداث برامج.
DONE: 0218 (a+b+c+d = 7+19+17+26 facts?)
DONE: 0216 (دكتور في الطب) — دفعات c,d,e (80 حقيقة جديدة، المواد 2–39) 2026-11-13
DONE: 0286 (دفعة a2، صور الصفحات 1-9) 2026-11-13
DONE: 0238 (دفعة b، صور الصفحات 1-7، 42 حقيقة) 2026-11-13
DONE: 0184 (دفعة c، 57 حقيقة، المواد 1-61) 2026-11-13
DONE: 0273 (دفعة c، 37 حقيقة، المواد 1-34) 2026-11-13
DONE: 0212 — لا حقائق جديدة: نسخة أقدم من 0238 (نفس المحتوى ما عدا قرارات 2018-2020 الموجودة فقط في 0238)؛ عند إعادة البناء: إزالة تكرار 0212-a مقابل 0238 2026-11-13
DONE: 0278 batch c (see raw/0278_c.jsonl), full coverage arts 1-33
DONE: 0282 batch b (raw/0282_b.jsonl)
DONE: 0279 batch b (raw/0279_b.jsonl)
DONE: 0274 batch b (raw/0274_b.jsonl) image-verified; note this doc uses percent marks (pass 70%, GPA 75%)
DONE: 0272 batch b (raw/0272_b.jsonl) image-verified (percent marks: pass 70, GPA 75; remedial pass 70)
DONE: 0275 batch d (raw/0275_d.jsonl), full coverage
DONE: 0271 batch c (raw/0271_c.jsonl)
DONE: 0277 batch c (raw/0277_c.jsonl)
DONE: 0280 batch b (raw/0280_b.jsonl)
DONE: 0268 batch b (raw/0268_b.jsonl) image-verified partly; last fact points table values from standard grad code
DONE: 0247 batch b (13 facts, text); 0244 batch b (29 facts, image-verified)
DONE: 0245 batch b (29 facts, image); 0230 batch b (9 facts, text; English source, Arabic Qs)
DONE: 0225 batch b (20 facts, text+image check of 12wk/300h; 12wk/300h from earlier verified a001); 0217 batch b (18 facts, image-verified; art 9-10,15 numbers from page 2)
DONE: 0260 batch b (16 facts, image-verified pages 1-2); 0128 batch b (13 facts, text)
DONE: 0164 batch b (8 facts, text); 0209 batch b (6 facts, image-verified; percentage fractions of salary NOT stated — ambiguous in source, flag to user)
DONE: 0161 batch b (29 facts, image-verified pages 2-4; confirms existing a006 max fine 50 JD)
DONE: 0171 batch b (44 facts, text; per-penalty/per-violation/procedure facts; article numbers follow existing a001-a018 cites, paragraph letters from OCR order — verify at final review)
DONE: 0170 batch b (18 facts, image-verified; old 1999 system overlaps 2024 instructions 0171 — log as overlapping versions); 0187 batch b (21 facts, image-verified p3)
DONE: 0185 batch b (27 facts, image-verified p2; 35 students/51%/60% GPA); 0201 batch b (28 facts, clean text)
DONE: 0196 batch b (42 facts, image-verified table z0196_top/bot; existing a001-a012 re-checked OK); 0222 batch b (17 facts, image p1 + text)
DONE: 0228 batch b (16 facts, image-verified p2); 0262 batch b (13 facts, image-verified table 1; 55 exempt hours)
NOTE 0262: table total says 55 hrs but listed rows sum to 58 — source inconsistency, add to decision log
DONE: 0263 batch b (11 facts, image-verified; NOTE program frozen from 2010/2011 per footnote 2010/19); 0270 batch b (12 facts, image-verified; 9 hrs, double fees)
DONE: 0252 batch b (11 facts, image-verified; parallel-program Arab-cert list marked 'لا يعمل به'); 0253 batch b (8 facts, image-verified)
DONE: 0257 batch b (11 facts, image-verified; NOTE art 5(c) 30/45 hrs vs art 8 45/55 hrs - different contexts, log it); 0283 batch b (13 facts, image-verified for pages 1-2; formulas verified from PDF render)
DONE: 0285 batch b (9 facts, image-verified); 0287 batch b (8 facts, image-verified). FIXED batch-a errors: 0287-a001 duration 4->6 semesters, 0285-a002 outside members 1->2 (patched raw/facts/train)
DONE: 0288 batch b (6 facts, image-verified from PDF render); 0281 batch b (18 facts, image-verified)
DONE: 0207 batch b (11 facts, image-verified); 0202 batch b (7 facts, image-verified). FIXED batch-a: 0202-a002 wording 'تخصم 10%'->'تحدد ... بنسبة 10%' (ambiguity), 0207-a003 cite -> 'قرار مجلس الأمناء رقم 2012/10 بتاريخ 2012/12/13' (raw/facts/train)
DONE: 0203 batch b (5 facts, image-verified); 0204 batch b (2 facts, image-verified; batch-a 0203/0204 facts checked vs images, no change)
DONE: 0234 batch b (42 facts, image-verified; all spec codes + footnotes; fn2 session date omitted for legibility)
DONE (gap review batch 1): 0218 batch e (33 facts: art 6 course lists/hours, art 9(c), art 10, 12, 13 + 2019/2020 transitional, art 18 h/t/y; image-verified for course tables & art 13, text for rest; one draft fact corrected after image check)
DONE (gap review batch 1): 0177 batch b (13 facts, text-verified, digits reliable; a-facts already cover grants/loans/work conditions)
DONE (gap review batch 1): 0182 batch b (10 facts, text-verified, digits reliable)
DONE (gap review batch 1): 0186 batch b (9 facts, image-verified); fixed 0186-a007 wording (art 14 says 'العلمية والداخلية لأكثر من يوم', no 'الخارجية'); batch-a 25 students/75% confirmed
DONE (gap review batch 1): 0193 batch b (8 facts, image-verified; PDF digits are reversed in extracted text, verified on render: 20 JD, 50 JD, 10/20 JD camps)
NOTE: 0177 art1 date (1988/8/7), 12/24 hrs, 3.5, 200 JD and 0182 decision 2023/31 on 2023/8/29 + article numbering confirmed on PDF render
DONE (gap review batch 1): 0166 batch b (9 facts, image-verified)
DONE (gap review batch 1): 0172 batch b (7 facts, image-verified; footnote ref no. 3ع/14847 omitted, illegible)
DONE (gap review batch 1): 0216 batch f (13 facts, image-verified: elective lists as in MD plan, 2022/30 & 2024/41 decisions, 11 hrs, 221 hrs, 408 40/60, 9-hr courses; assessment distributions already covered by batch a/d facts)
DONE (gap review batch 1): 0214 batch d (7 facts, text-verified, lists match elective tables); 0230 batch c (2 facts: ID card, proctor may confiscate; other gaps were false positives from English form text vs Arabic facts)
DONE (gap review batch 2): 0247 batch c (11 facts, text-verified digits reliable: dean/dept-head/registrar procedures)
DONE (gap review batch 2): 0218 residual chunks checked vs facts a/b/c/d/e — all covered, no new facts
DONE (gap review batch 2): 0275 checked all gap chunks vs facts a-d — all covered, no new facts
DONE (gap review batch 2): 0196 checked (table facts a/b cover chunk 003); 0229 batch b (6 facts, art. 4 items 5-19 verified on image)
DONE (gap review batch 2): 0256 batch b (15 facts, image-verified: Arab certs, staff kids, special categories, Royal Court, dismissed, arts 11-14); 0281 checked, covered; fixed 0256-a002 cite
DONE (gap review batch 2): 0214 batch e (3 facts, art. 17 exemption/plan/committee); 0248 batch b (12 facts, arts 1-15 text-verified)
DONE (gap review batch 2): 0216 checked all gap chunks vs d018/d019/d020/f012/f013 — covered, no new facts
DONE (gap review batch 3): 0267 batch b (6, image); 0249 batch b (5, image + pdftotext footnote)
DONE (gap review batch 3): 0232 checked covered; 0255 batch b (6, image); 0282 checked covered; 0269 batch b (5, text)
DONE (gap review batch 3): 0246 batch b (6, text; arts 6-8,10(ج),11,13,14); 0199 chunk 002 is footnotes only (decision numbers illegible; half-dinar cheque-stamp deduction footnote of unclear attachment) — no facts; 0263 and 0244 checked covered
DONE (gap review batch 4 part1): 0271 covered; 0181 batch b (4, image date 2017/6/1); 0224 batch b (5, image); 0198 batch b (1, image: from 2012/2013)
DONE (gap review batch 4 part2): 0259 batch b (25 facts, image; full mapping table of community-college diploma specialties); 0176/0195 pending review
DONE (gap review batch 4 part3): 0176 batch b (6, image; arts 1,5,6,8,9,11-12); 0195 batch b (2, text)
DONE (gap review batch 4 part4): 0239 batch b (6, image); 0188 batch b (2, text); 0167 batch b (1, text); 0173 and 0164 checked covered
DONE (gap review batch 4 part5): 0241 batch b (3, image); 0178 batch b (5, text); 0233 batch b (7, image/text); 0286 chunk is footnotes only; 0266 pending image
DONE (gap review batch 4 part6): 0191 batch b (3, image); 0266 batch b (3, image); 0289 batch b (3, text); 0251 chunk is footnote only
DONE: final rebuild after gap review (2958 facts; 8810 pairs; leaks 0; numbers 0; 64 dup pairs dropped pending rewording); SCHEMA.md updated; zip regenerated
DONE: reworded 64 duplicate questions; rebuild -> 8,874 pairs (train 7,986 / val 888), dups 0, leaks 0, numbers 0
DONE: fidelity check text-verified numeric facts — 0201 (28 facts) matched images, 0 errors. Remaining of 344: 0218,0216,0278,0273,0275,0184,0271,0279,0277,0214,0269,0177,0248,0173,0280,0247,0283,0225,0230,0171,0182,0190,0288
DONE: fidelity 0216 first 10 numeric facts (a001-a014) matched images, 0 errors (0201 also 0 errors). Next: 0216 remaining 50, then 0218 (69)
DONE: DECISIONS.md written; fidelity check stopped by user decision (0201, 0216 first 10: 0 errors)
