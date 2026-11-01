# 정리본 표의 줄을 기준의 「파일 안의 짜임」대로 다시 늘어놓음.
import sys,re,glob,os
D=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORD={
'1s':['세력','계급','작위','보직','가진 것','출신','이력','관계','평판','생김새와 몸','기호와 습관'],
'1b':['성격','감정 반응','말투와 말버릇','가치관','바라는 것','판단','사람을 대하는 태도','전략과 전술 성향','능력'],
'2':['소속','사람과 자리','규모','기반','관계','평판','목표','민심'],
'3':['소속','지형','이어진 곳','시설','겉모습','주둔','인구와 주민','경제','관계','평판'],
'4':['정해진 것','평판'],'5':['소속','겉모습','성능','역할','평판'],
'6':['내용','인용','따르는 쪽','평판'],'7':['경과','남긴 것','평판'],
'8':['하는 법','조건','강약','평판'],'9':['걸린 시간'],'10':['사례'],'11':['수']}
def year(s):
    m=re.search(r'\d+',s)
    if not m: return 10**6
    v=int(m.group()); 
    return v-5000 if s.startswith('서기') else v
def cells(r): return [c.strip() for c in r.strip().strip('|').split('|')]
def sort_rows(rows,key):
    order=ORD[key]; idx={r:i for i,r in enumerate(rows)}
    first={}
    for r in rows:
        t=cells(r)[0]; first.setdefault(t,(year(cells(r)[2]),idx[r]))
    def tkey(t):
        if key in('1s','1b','3','4','5','6','8','9'): return (t,)
        if key=='7': return first[t]
        return (first[t][1],)   # 2, 10: 처음 나온 차례
    def rkey(r):
        c=cells(r); io=order.index(c[1]) if c[1] in order else 99
        if key=='11': return (year(c[2]),idx[r])
        return (tkey(c[0]),io,year(c[2]) if key not in('10',) else 0,idx[r])
    return sorted(rows,key=rkey)
for f in sorted(glob.glob(D+'/[0-9]*_*.md')):
    n=os.path.basename(f).split('_')[0]
    L=open(f,encoding='utf-8').read().split('\n'); out=[]; i=0; sub=None
    while i<len(L):
        l=L[i]; out.append(l)
        if l.startswith('### 사실'): sub='1s'
        if l.startswith('### 바탕'): sub='1b'
        if l.startswith('|---'):
            j=i+1; rows=[]
            while j<len(L) and L[j].startswith('|'): rows.append(L[j]); j+=1
            k=sub if n=='1' else n
            out+=sort_rows(rows,k); i=j; continue
        i+=1
    open(f,'w',encoding='utf-8').write('\n'.join(out))
print('sorted')
