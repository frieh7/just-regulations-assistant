import sys; sys.path.insert(0,'/home/claude/scripts')
from facts_lib import save
N="تعليمات منازل الطلبة لسنة 1999"
F=[]
def r(c,a,q1,q2,q3): F.append(("rule",[1],c,a,q1,q2,q3))
r("المادة 14","رئيس الجامعة مسؤول عن تنفيذ أحكام تعليمات منازل الطلبة.","من المسؤول عن تنفيذ تعليمات منازل الطلبة؟","هل رئيس الجامعة مسؤول عن تنفيذ تعليمات المنازل؟","مين بنفذ تعليمات منازل الطلبة؟")
save("0167",N,F,"b",verified="text")
print(len(F))
